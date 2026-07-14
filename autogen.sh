#!/bin/sh

printf '%s\n' \
	'autogen.sh is no longer used by ddccontrol-db.' \
	'Packagers should run ./configure, make, and make install directly.' \
	'No Autoconf, Automake, Intltool, or Libtool bootstrap step is required.'

exit 0
