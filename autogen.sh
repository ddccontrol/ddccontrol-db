#!/bin/sh

echo "Running libtoolize..."
libtoolize --copy --force --automake

echo "Running gettextize..."
gettextize --copy --force --no-changelog
mv Makefile.am~ Makefile.am

echo "Running intltoolize..."
intltoolize --copy --force --automake

sed() { local fname perm; fname=$(eval echo \$$#); perm="$(stat -c "%a" "$fname")"; env sed "$@"; chmod "$perm" "$fname"; }
sed -e "s|\@INSTOBJEXT\@|.mo|" -i'~' po/Makefile.in.in
sed -e "s|\@CATOBJEXT\@|.gmo|" -i'~' po/Makefile.in.in
sed -e "s|\@GENCAT\@|gencat|" -i'~' po/Makefile.in.in
unset -f sed

echo "Running aclocal..."
aclocal -I m4

echo "Running autoconf..."
autoconf

echo "Running automake..."
automake -a --copy
