#!/usr/bin/perl
#
# Check that every monitor control typed "list" in db/options.xml.in carries at
# least one <value> entry in the monitor profile that uses it.
#
# Numeric values are not inherited from options.xml.in, so a control written as
#   <control id="foo" address="0x12"/>
# loads as a list with no selectable choices. `ddccontrol -i`, and therefore
# `make check-db`, reports such a profile as OK, so this needs its own check.
#
# Profiles listed in db/known-empty-list-controls are grandfathered: they had
# this condition before the check existed and need their hardware owners to
# supply the correct model-specific values.
#
# Usage: perl scripts/check-list-values.pl [dbdir]

use strict;
use warnings;
use XML::Parser;

my $db       = $ARGV[0] || 'db';
my $optfile  = "$db/options.xml.in";
my $baseline = "$db/known-empty-list-controls";

# Keep element order and let an XML parser handle whitespace, quotes, entities
# and comments. Cache shared profiles, which may be included many times.
my %documents;
sub document {
    my ($path) = @_;
    return $documents{$path} if exists $documents{$path};
    my (@stack, $root);
    my $parser = XML::Parser->new(Handlers => {
        Start => sub {
            my ($parser, $tag, %attributes) = @_;
            my $node = { tag => $tag, attributes => \%attributes, children => [] };
            if (@stack) { push @{$stack[-1]{children}}, $node; }
            else { $root = $node; }
            push @stack, $node;
        },
        End => sub { pop @stack; },
        ExternEnt => sub { die "external entities are not supported in $path\n"; },
    });
    eval { $parser->parsefile($path); 1 }
        or die "cannot parse $path: $@";
    return $documents{$path} = $root;
}

# ddccontrol processes controls within each <controls> block in options order.
my @options;
sub option_controls {
    my ($node) = @_;
    if ($node->{tag} eq 'control') { push @options, $node; }
    else { option_controls($_) for @{$node->{children}}; }
}
option_controls(document($optfile));

my %grandfathered;
if (-e $baseline) {
    open(my $base, '<', $baseline) or die "cannot read $baseline: $!\n";
    while (<$base>) {
        s/#.*//;
        next unless /\S/;
        my @pair = split;
        die "invalid entry in $baseline at line $.\n" unless @pair == 2;
        my $key = join ' ', @pair;
        die "duplicate entry '$key' in $baseline\n" if $grandfathered{$key}++;
    }
    close($base);
}

sub address_of {
    my ($control, $name) = @_;
    my $raw = $control->{attributes}{address};
    die "missing control address in $name\n" unless defined $raw;
    die "invalid control address '$raw' in $name\n"
        unless $raw =~ /\A(?:0[xX][0-9a-fA-F]+|0[0-7]*|[1-9][0-9]*)\z/;
    my $address = $raw =~ /^0/ ? oct($raw) : 0 + $raw;
    die "control address out of range in $name: $raw\n" if $address > 255;
    return $address;
}

# Capabilities are nested parenthesized sections, not XML. Keep value lists
# attached to their VCP code so removing a value cannot disable another code.
sub caps_list {
    my ($tokens, $position, $nested, $name) = @_;
    my @items;
    while ($$position < @$tokens) {
        my $token = $tokens->[$$position++];
        if ($token eq '(') {
            push @items, caps_list($tokens, $position, 1, $name);
        } elsif ($token eq ')') {
            die "unbalanced caps in $name\n" unless $nested;
            return \@items;
        } else {
            push @items, $token;
        }
    }
    die "unbalanced caps in $name\n" if $nested;
    return \@items;
}

sub apply_vcp {
    my ($items, $caps, $add, $name) = @_;
    for (my $i = 0; $i < @$items; $i++) {
        my $code = $items->[$i];
        die "invalid VCP code in $name\n" if ref $code;
        # Some profiles advertise adjacent two-digit codes without spaces.
        if ($code =~ /\A[0-9a-fA-F]{3,}\z/) {
            splice @$items, $i, 1, ($code =~ /.{1,2}/g);
            $code = $items->[$i];
        }
        my $values = ref($items->[$i + 1]) ? $items->[++$i] : undef;
        if (lc($code) eq 'vcp' && $values) {
            apply_vcp($values, $caps, $add, $name);
            next;
        }
        die "invalid VCP code '$code' in $name\n"
            unless $code =~ /\A[0-9a-fA-F]{2}\z/;
        my %values;
        for my $value (@{$values || []}) {
            next if ref $value;
            die "invalid VCP value '$value' in $name\n"
                unless $value =~ /\A[0-9a-fA-F]{1,4}\z/;
            $values{hex($value)} = 1;
        }
        $code = hex($code);
        if ($add) {
            $caps->{$code} = keys(%values) ? \%values : undef;
        } elsif (exists $caps->{$code}) {
            if (keys(%values) && defined $caps->{$code}) {
                delete @{$caps->{$code}}{keys %values};
                delete $caps->{$code} unless keys %{$caps->{$code}};
            } else {
                delete $caps->{$code};
            }
        }
    }
}

sub caps_sections {
    my ($items, $caps, $add, $name) = @_;
    for (my $i = 0; $i < @$items; $i++) {
        my $item = $items->[$i];
        if (ref $item) {
            caps_sections($item, $caps, $add, $name);
        } elsif (ref($items->[$i + 1])) {
            my $section = $items->[++$i];
            apply_vcp($section, $caps, $add, $name) if $item eq 'vcp';
        }
    }
}

sub controls_of {
    my ($name, $defined, $active, $caps) = @_;
    die "invalid include name '$name'\n" unless $name =~ /\A[A-Za-z0-9_-]+\z/;
    die "include cycle involving $name\n" if $active->{$name};
    local $active->{$name} = 1;
    my @found;
    my $root = document("$db/monitor/$name.xml");
    for my $node (@{$root->{children}}) {
        if ($node->{tag} eq 'caps') {
            # Match ddccontrol: removal precedes addition within one element,
            # and changes made by an include remain in effect in its caller.
            for my $operation ('remove', 'add') {
                my $text = $node->{attributes}{$operation};
                next unless defined $text;
                my @tokens = $text =~ /([()]|[^()\s]+)/g;
                my $position = 0;
                caps_sections(caps_list(\@tokens, \$position, 0, $name),
                    $caps, $operation eq 'add', $name);
            }
        }
        elsif ($node->{tag} eq 'include') {
            my $file = $node->{attributes}{file};
            die "missing include file in $name\n" unless defined $file;
            push @found, controls_of($file, $defined, $active, $caps);
        }
        elsif ($node->{tag} eq 'controls') {
            my %controls;
            for my $control (@{$node->{children}}) {
                next unless $control->{tag} eq 'control';
                my $id = $control->{attributes}{id};
                die "missing control id in $name\n" unless defined $id;
                $controls{$id} ||= $control;
            }
            for my $option (@options) {
                my $id = $option->{attributes}{id};
                my $control = $controls{$id} or next;
                my $address = address_of($control, $name);
                next unless exists $caps->{$address};
                # The first definition of an address wins, even if the IDs or
                # types differ. Later included definitions are not active.
                next if $defined->{$address}++;
                next unless ($option->{attributes}{type} || '') eq 'list';
                my %value_ids = map { $_->{attributes}{id} => 1 }
                    grep { $_->{tag} eq 'value' && defined $_->{attributes}{id} }
                    @{$option->{children}};
                my $has_value = grep {
                    $_->{tag} eq 'value'
                        && defined $_->{attributes}{id}
                        && defined $_->{attributes}{value}
                        && $value_ids{$_->{attributes}{id}}
                } @{$control->{children}};
                push @found, [ $id, $has_value, $name ];
            }
        }
    }
    return @found;
}

opendir(my $dir, "$db/monitor") or die "cannot read $db/monitor: $!\n";
my @profiles = sort map { s/\.xml$//r } grep { /\.xml$/ } readdir($dir);
closedir($dir);

my ($failed, $skipped) = (0, 0);
my %used;
for my $profile (@profiles) {
    # As in ddccontrol -i, start with every address available, then apply the
    # profile's explicit capability changes. No hardware caps are needed.
    my %caps = map { $_ => undef } 0 .. 255;
    for my $control (controls_of($profile, {}, {}, \%caps)) {
        my ($id, $has_value, $origin) = @$control;
        next if $has_value;
        my $key = "$profile $id";
        if ($grandfathered{$key}) {
            $used{$key} = 1;
            $skipped++;
            next;
        }
        printf STDERR
            "%s: list control '%s' (declared in %s) has no <value> entries\n",
            $profile, $id, $origin;
        $failed++;
    }
}

my @stale = sort grep { !$used{$_} } keys %grandfathered;
for my $key (@stale) {
    print STDERR "stale exception '$key' in $baseline; remove this entry\n";
}
if ($failed) {
    print STDERR "\n$failed list control(s) would load with no selectable values.\n";
    print STDERR "Add <value id=\"...\" value=\"...\"/> entries to the monitor profile.\n";
}
exit 1 if $failed || @stale;

printf "checked %d profiles, no empty list controls (%d grandfathered)\n",
    scalar(@profiles), $skipped;
exit 0;
