SHELL := /bin/bash
PGDATABASE ?= arachnid
PG_BINDIR  := $(shell pg_config --bindir)
PRIME_DB_USER := $(shell echo $PRIME_DB_USER)
PRIME_DB_PASS := $(shell echo $PRIMIE_DB_PASS)
pg         := ${PG_BINDIR}/psql -h babel -U arachnid -d ${PGDATABASE}


.PHONY: is-ready
is-ready:
	until ${PG_BINDIR}/pg_isready -h babel -U postgres ; do sleep 5 ; done

.PHONY: create-db
create-db:
	${PG_BINDIR}/createuser -d -s -U postgres -w  arachnid  || true
	${PG_BINDIR}/createdb -l en_US.utf8 -w -U postgres ${PGDATABASE}
	./manage.py db upgrade

.PHONY: generate-fake
generate-fake:
	./manage.py generate_fake

.PHONY: drop-db
drop-db:
	${PG_BINDIR}/dropdb -U postgres -w --if-exists ${PGDATABASE}

.PHONY: reset
reset: is-ready drop-db create-db

.PHONY: test
test:
	./manage.py test

.PHONY: uwsgi
uwsgi:
	python worker.py &
	uwsgi --ini production.ini

.PHONY: run
run: is-ready uwsgi