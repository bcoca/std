#!/usr/bin/env perl
# This is mostly an adaptaion of a couple of existing ejabberd auth scripts

use strict;
use Sys::Syslog;
use Authen::Htpasswd;

openlog $0, 'ndelay', 'auth';
$SIG{__WARN__} = sub { syslog('warning', $_[0]);};

my $pwfilepath = $ARGV[0] || "/etc/ejabberd/.htpasswd";
my $debug = $ARGV[1] || 0;
my $pwfile = Authen::Htpasswd->new($pwfilepath, { encrypt_hash => 'md5'});

while(1)
{
    my $buf = "";
    syslog ('info',"waiting for packet") if $debug;
    my $nread = sysread STDIN, $buf, 2;
    do { syslog ('info',"port closed"); exit; } unless $nread == 2;
    my $len = unpack "n", $buf;
    $nread = sysread STDIN, $buf, $len;
    do { syslog ('info',"port closed"); exit; } unless $nread == $len;

    my($op, $user, $domain, $password) = split /:/,$buf;
    # Filter dangerous characters
    $user     =~ s/["\n\r'\$`]//g;
    $password =~ s/["\n\r'\$`]//g;
    $domain   =~ s/["\n\r'\$`]//g;
    $user     = lc $user;
    $domain   = lc $domain;
    syslog('info',"Request (%s) %s@%s", $op, $user, $domain);

    my $jid = "$user\@$domain";
    my $result;

    SWITCH:
    {
        $op eq 'auth' and do
        {
	    if ( $pwfile->lookup_user($user)) {
            $result = ($pwfile->check_user_password($user, $password)) ? 1: 0;
	    } else {
		if ( $pwfile->lookup_user($jid) ) {
           $result = ($pwfile->check_user_password($jid, $password)) ? 1: 0;
		}
	    }
            syslog('info', "Auth result: %s", $result);
        }, last SWITCH;

        $op eq 'setpass' and do
        {
            $pwfile->update_user($user, $password);
            $result = 1;
            syslog('info', "%s password updated", $user);
        }, last SWITCH;

        $op eq 'isuser' and do
        {
            # Password is null. Return 1 if the user $user \ @ $domain exist.
            $result = ($pwfile->lookup_user($user) || $pwfile->lookup_user($jid)) ? 1: 0;
            syslog('info', "%s exists is %s", $user, $result);
        }, last SWITCH;
    };
    my $out = pack "nn", 2, $result ? 1: 0;
    syslog('info',"sending result=%d", $result);
    syswrite STDOUT, $out;
}
