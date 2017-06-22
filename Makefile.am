SUBDIRS= db po

EXTRA_DIST = config.rpath intltool-extract.in intltool-merge.in intltool-update.in xml2h.pl po/POTFILES

# needed to conform GNU standards
# TODO: more sophisticated solution is welcome
README: README.md
	cp $< $@

check-db:
	cd db && make check-db
