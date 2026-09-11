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

my $db       = $ARGV[0] || 'db';
my $optfile  = "$db/options.xml.in";
my $baseline = "$db/known-empty-list-controls";

# --- which control ids are list-typed -------------------------------------
my %is_list;
open(my $opt, '<', $optfile) or die "cannot read $optfile: $!\n";
while (<$opt>) {
    $is_list{$1} = 1 if /<control\s[^>]*id="([^"]+)"[^>]*type="list"/;
    $is_list{$1} = 1 if /<control\s[^>]*type="list"[^>]*id="([^"]+)"/;
}
close($opt);

# --- grandfathered "profile control" pairs --------------------------------
my %grandfathered;
if (open(my $base, '<', $baseline)) {
    while (<$base>) {
        chomp;
        s/#.*//;
        s/^\s+|\s+$//g;
        next unless length;
        $grandfathered{$_} = 1;
    }
    close($base);
}

# --- collect controls declared by one profile, following includes ---------
sub controls_of {
    my ($name, $seen) = @_;
    $seen ||= {};
    return () if $seen->{$name}++;
    my $path = "$db/monitor/$name.xml";
    return () unless -f $path;

    open(my $fh, '<', $path) or die "cannot read $path: $!\n";
    my $text = do { local $/; <$fh> };
    close($fh);

    # Commented-out controls are parked for future investigation and must not
    # be reported. Strip comment blocks before looking at anything else.
    $text =~ s/<!--.*?-->//gs;

    my @found;
    my ($open_id, $saw_value);
    for my $line (split /\n/, $text) {
        if (defined $open_id) {
            $saw_value = 1 if $line =~ /<value\s/;
            if ($line =~ m{</control>}) {
                push @found, [ $open_id, $saw_value, $name ];
                undef $open_id;
            }
            next;
        }
        if ($line =~ /<control\s[^>]*id="([^"]+)"/) {
            my $id = $1;
            if ($line =~ m{/>\s*$}) {
                push @found, [ $id, 0, $name ];
            } else {
                $open_id   = $id;
                $saw_value = ($line =~ /<value\s/) ? 1 : 0;
            }
        }
        elsif ($line =~ /<include\s[^>]*file="([^"]+)"/) {
            push @found, controls_of($1, $seen);
        }
    }
    return @found;
}

# --- walk every profile ---------------------------------------------------
opendir(my $dir, "$db/monitor") or die "cannot read $db/monitor: $!\n";
my @profiles = sort map { s/\.xml$//r } grep { /\.xml$/ } readdir($dir);
closedir($dir);

my $failed = 0;
my $skipped = 0;
for my $profile (@profiles) {
    for my $c (controls_of($profile)) {
        my ($id, $has_value, $origin) = @$c;
        next unless $is_list{$id};
        next if $has_value;
        if ($grandfathered{"$profile $id"}) { $skipped++; next; }
        printf STDERR
            "%s: list control '%s' (declared in %s) has no <value> entries\n",
            $profile, $id, $origin;
        $failed++;
    }
}

if ($failed) {
    print STDERR "\n$failed list control(s) would load with no selectable values.\n";
    print STDERR "Add <value id=\"...\" value=\"...\"/> entries to the monitor profile.\n";
    exit 1;
}

printf "checked %d profiles, no empty list controls (%d grandfathered)\n",
    scalar(@profiles), $skipped;
exit 0;
