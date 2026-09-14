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

sub controls_of {
    my ($name, $defined, $active) = @_;
    die "invalid include name '$name'\n" unless $name =~ /\A[A-Za-z0-9_-]+\z/;
    die "include cycle involving $name\n" if $active->{$name};
    local $active->{$name} = 1;
    my @found;
    my $root = document("$db/monitor/$name.xml");
    for my $node (@{$root->{children}}) {
        if ($node->{tag} eq 'include') {
            my $file = $node->{attributes}{file};
            die "missing include file in $name\n" unless defined $file;
            push @found, controls_of($file, $defined, $active);
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
    for my $control (controls_of($profile, {}, {})) {
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
