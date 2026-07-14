#!/bin/sh

available_languages()
{
	sed -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' po/LINGUAS
}

selected_languages()
{
	available=$(available_languages)

	if test "${LINGUAS+x}" = x; then
		requested=$LINGUAS
	elif test "$CONFIG_NLS" = no; then
		requested=
	else
		requested=$available
	fi

	for language in $requested; do
		for candidate in $available; do
			if test "$language" = "$candidate"; then
				printf '%s\n' "$language"
				break
			fi
		done
	done
}

load_build_config()
{
	if test ! -f ./config.sh; then
		echo "Run ./configure before make." >&2
		exit 1
	fi

	. ./config.sh

	prefix_value=$CONFIG_PREFIX
	if test "${prefix+x}" = x; then prefix_value=$prefix; fi
	if test "${PREFIX+x}" = x; then prefix_value=$PREFIX; fi

	if test "$CONFIG_DATADIR_EXPLICIT" = yes; then
		datadir_value=$CONFIG_DATADIR
	else
		datadir_value=$prefix_value/share
	fi
	if test "${datadir+x}" = x; then datadir_value=$datadir; fi
	if test "${DATADIR+x}" = x; then datadir_value=$DATADIR; fi

	if test "$CONFIG_LOCALEDIR_EXPLICIT" = yes; then
		localedir_value=$CONFIG_LOCALEDIR
	else
		localedir_value=$datadir_value/locale
	fi
	if test "${localedir+x}" = x; then localedir_value=$localedir; fi
	if test "${LOCALEDIR+x}" = x; then localedir_value=$LOCALEDIR; fi

	if test "$CONFIG_DBDIR_EXPLICIT" = yes; then
		dbdir_value=$CONFIG_DBDIR
	else
		dbdir_value=$datadir_value/ddccontrol-db
	fi
	if test "${dbdir+x}" = x; then dbdir_value=$dbdir; fi
	if test "${DBDIR+x}" = x; then dbdir_value=$DBDIR; fi

	destdir_value=${DESTDIR-}
}
