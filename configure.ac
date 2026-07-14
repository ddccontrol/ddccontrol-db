dnl Temporary compatibility shim for downstream packages that still invoke
dnl autoreconf. Normal builds use the maintained configure script directly.
AC_INIT([ddccontrol-db], m4_esyscmd_s([sed -n '1p' VERSION]))
AC_CONFIG_SRCDIR([VERSION])

dnl Declare the option so the generated configure accepts Gentoo's econf flag.
dnl configure.impl performs the actual option handling and dependency checks.
AC_ARG_ENABLE([nls])

AC_CONFIG_COMMANDS_PRE([
  eval "set x $ac_configure_args"
  shift
  exec "$srcdir/configure.impl" "$[]@"
])

AC_OUTPUT
