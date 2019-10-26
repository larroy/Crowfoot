#!/usr/bin/perl
use File::Copy;

$MACHINE = `uname -n` or die "uname";
chomp $MACHINE;
$KERNEL = `uname -r` or die "uname";
chomp $KERNEL;

mkdir $MACHINE or die "mkdir: $!";
chdir $MACHINE or die "chdir: $!";

@date = gmtime(time);
$date = join("-",$date[3],$date[4]+1,$date[5]+1900);

system("tar cpvvjf $MACHINE-$date-etc.tar.bz2 /etc") == 0 or die;
system("dpkg --get-selections > $MACHINE-$date.sel") == 0 or die;
system("lspci > $MACHINE-$date-lspci.txt") == 0 or die;
if ( -f "/boot/config") {
	copy("/boot/config","./$MACHINE-$date-config-$KERNEL") or die "copy: $!";
}	
