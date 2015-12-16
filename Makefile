SHELL := /bin/bash
PGDATABASE ?= arachnid
PG_BINDIR  := $(shell pg_config --bindir)
pg         := ${PG_BINDIR}/psql -h babel -U ${PRIME_DB_USER} -d ${PGDATABASE}

.PHONY: create-db
create-db:
	until ${PG_BINDIR}/pg_isready -q ; do sleep 5 ; done
	${PG_BINDIR}/createuser -d -s -U postgres -w  ${PRMIE_DB_USER}
	${PG_BINDIR}/createdb -l en_US.utf8 -w -U postgres ${PGDATABASE}
	./manage.py db upgrade

.PHONY: generate-fake
generate-fake:
	./manage.py generate_fake

.PHONY: drop-db
drop-db:
	${PG_BINDIR}/dropdb -U postgres -w --if-exists ${PGDATABASE}

.PHONY: reset
reset: drop-db create-db

.PHONY: test
test:
	./manage.py test
