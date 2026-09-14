#!/usr/bin/perl
use strict;
use warnings;
use Test::More;
use File::Temp qw(tempdir);
use FindBin;

my $checker = $ARGV[0] || "$FindBin::Bin/check-list-values.pl";
my $options = <<'XML';
<options>
  <group name="Tests"><subgroup name="Controls">
    <control id="scalar" type="value" name="Scalar"/>
    <control id="mode" type="list" name="Mode">
      <value id="on" name="On"/>
    </control>
    <control id="other" type="list" name="Other">
      <value id="on" name="On"/>
    </control>
  </subgroup></group>
</options>
XML
my $empty = '<control id="mode" address="0xf9"/>';
my $full = <<'XML';
<control id="mode" address="0xf9">
  <value id="on" value="1"/>
</control>
XML

sub monitor {
    return '<monitor name="Test" init="standard">' . $_[0] . '</monitor>';
}
sub controls {
    return '<controls>' . $_[0] . '</controls>';
}
sub check {
    my ($name, %args) = @_;
    subtest $name => sub {
        my $dir = tempdir(CLEANUP => 1);
        mkdir "$dir/monitor" or die "mkdir: $!";
        my %files = (
            'options.xml.in' => $args{options} || $options,
            'known-empty-list-controls' => $args{baseline} || '',
            %{$args{files} || {}},
        );
        $files{'monitor/TEST.xml'} = monitor($args{xml}) if defined $args{xml};
        for my $file (keys %files) {
            open(my $fh, '>', "$dir/$file") or die "write $file: $!";
            print {$fh} $files{$file};
            close($fh) or die "close $file: $!";
        }
        # Capture both streams without shell quoting or external utilities.
        my $pid = open(my $pipe, '-|');
        die "fork: $!" unless defined $pid;
        if (!$pid) {
            open(STDERR, '>&', STDOUT) or die "redirect: $!";
            exec $^X, $checker, $dir;
            die "exec: $!";
        }
        my $output = do { local $/; <$pipe> };
        close($pipe);
        my $status = $?;
        is($status & 127, 0, 'checker exited normally');
        if ($args{exit} eq 'nonzero') {
            isnt($status >> 8, 0, 'rejected invalid input') or diag $output;
        } else {
            is($status >> 8, $args{exit}, 'exit status') or diag $output;
        }
        like($output, $args{message}, 'diagnostic') if $args{message};
        unlike($output, $args{absent}, 'no spurious diagnostic') if $args{absent};
    };
}

for my $case (
    ['self-closing', $empty],
    ['explicit empty', '<control id="mode" address="0xf9"></control>'],
    ['multiline attributes', "<control\n address='0xf9'\n id='mode'\n/>"],
    ['single quotes', "<control id='mode' address='0xf9'/>"],
    ['commented value', '<control id="mode" address="0xf9"><!-- <value id="on" value="1"/> --></control>'],
) {
    check($case->[0], xml => controls($case->[1]), exit => 1,
        message => qr/TEST: list control 'mode'.*has no <value> entries/);
}
check('populated', xml => controls($full), exit => 0);
check('inline populated', xml => controls('<control id="mode" address="0xf9"><value id="on" value="1"/></control>'), exit => 0);
check('numeric zero', xml => controls($full =~ s/value="1"/value="0"/r), exit => 0);
check('commented control', xml => controls("<!-- $empty -->"), exit => 0);
check('adjacent controls', xml => controls($full . '<control id="other" address="0xf8"/>'), exit => 1,
    message => qr/TEST: list control 'other'/);
check('multiline options', xml => controls($empty), exit => 1,
    options => $options =~ s/id="mode" type="list"/id='mode'\n type='list'/r,
    message => qr/TEST: list control 'mode'/);
check('comments in options', xml => controls($empty), exit => 0,
    options => $options =~ s{(<control id="mode".*?</control>)}{<!-- $1 -->}sr);
check('missing numeric value', xml => controls('<control id="mode" address="0xf9"><value id="on"/></control>'), exit => 1);
check('unknown choice', xml => controls('<control id="mode" address="0xf9"><value id="unknown" value="1"/></control>'), exit => 1);
check('malformed XML', xml => '<controls>' . $empty, exit => 'nonzero',
    message => qr/cannot parse/);

check('active exception with whitespace and comment', xml => controls($empty),
    baseline => "  TEST\tmode  # existing control\n", exit => 0,
    message => qr/1 grandfathered/);
check('exception for populated control is stale', xml => controls($full),
    baseline => "TEST mode\n", exit => 1, message => qr/stale exception 'TEST mode'/);
check('exception for removed control is stale', xml => controls(''),
    baseline => "TEST mode\n", exit => 1, message => qr/stale exception 'TEST mode'/);
check('exception for removed profile is stale', xml => controls($full),
    baseline => "REMOVED mode\n", exit => 1, message => qr/stale exception 'REMOVED mode'/);
check('removing stale exception passes', xml => controls($full), exit => 0);

my %parent = ('monitor/BASE.xml' => monitor(controls($empty)));
my $include = '<include file="BASE"/>';
check('inherited empty control', xml => $include, files => \%parent,
    baseline => "BASE mode\n", exit => 1,
    message => qr/TEST: list control 'mode' \(declared in BASE\)/);
check('populated override before include', xml => controls($full) . $include,
    files => \%parent, baseline => "BASE mode\n", exit => 0);
check('include before populated definition still wins', xml => $include . controls($full),
    files => \%parent, baseline => "BASE mode\n", exit => 1,
    message => qr/TEST: list control 'mode' \(declared in BASE\)/);
check('overrides compare numeric addresses, not IDs',
    xml => controls($full =~ s/id="mode" address="0xf9"/id="other" address="249"/r) . $include,
    files => \%parent, baseline => "BASE mode\n", exit => 0);
check('scalar override also occupies address',
    xml => controls('<control id="scalar" address="0371"/>') . $include,
    files => \%parent, baseline => "BASE mode\n", exit => 0);
check('same ID at another address does not override',
    xml => controls($full =~ s/0xf9/0xf8/r) . $include,
    files => \%parent, baseline => "BASE mode\n", exit => 1,
    message => qr/TEST: list control 'mode' \(declared in BASE\)/);
check('options order decides within a controls block',
    xml => controls($empty . '<control id="scalar" address="0xf9"/>'), exit => 0);
check('repeated include retains first definition', xml => $include . $include,
    files => { 'monitor/BASE.xml' => monitor(controls($full)) }, exit => 0);
check('nested includes preserve overrides', xml => controls($full) . '<include file="MIDDLE"/>',
    files => { %parent, 'monitor/MIDDLE.xml' => monitor($include) },
    baseline => "BASE mode\nMIDDLE mode\n", exit => 0);
check('multiline include', xml => "<include\n file='BASE'\n/>", files => \%parent,
    baseline => "BASE mode\n", exit => 1, message => qr/TEST: list control 'mode'/);
check('missing include fails', xml => '<include file="MISSING"/>', exit => 'nonzero',
    message => qr/cannot parse/);
check('include cycle fails', xml => '<include file="TEST"/>', exit => 'nonzero',
    message => qr/include cycle/);

done_testing();
