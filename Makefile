SHELL := /bin/bash
PGDATABASE ?= arachnid
PG_BINDIR  := $(shell pg_config --bindir)
PRIME_DB_USER := $(shell echo $PRIME_DB_USER)
PRIME_DB_PASS := $(shell echo $PRIMIE_DB_PASS)
pg         := ${PG_BINDIR}/psql -h babel -U arachnid -d ${PGDATABASE}
DB_LIST := $(shell ${PG_BINDIR}/psql -h babel -U postgres -l)


.PHONY: is-ready
is-ready:
	until ${PG_BINDIR}/pg_isready -h babel -U postgres ; do sleep 5 ; done

.PHONY: create-db
create-db:
	${PG_BINDIR}/createuser -h babel -d -s -U postgres -w arachnid  || true
	${PG_BINDIR}/createdb -h babel -l en_US.utf8 -w -U postgres ${PGDATABASE}
	./manage.py db upgrade

.PHONY: generate-fake
generate-fake:
	./manage.py generate_fake

.PHONY: drop-db
drop-db:
	${PG_BINDIR}/dropdb -h babel -U postgres -w --if-exists ${PGDATABASE}

.PHONY: is-ready first-setup-check
first-setup-check:
@echo First Setup Check
is_setup := $(${PG_LIST} | grep arachnid -q)
(${is_setup}="0",,reset)

.PHONY: reset
reset: is-ready drop-db create-db

.PHONY: test
test:
	./manage.py test

.PHONY: create-db-local
create-db-local:
	${PG_BINDIR}/createdb ${PGDATABASE}
	./manage.py db upgrade

.PHONY: reset-local
reset-local:
	${PG_BINDIR}/dropdb --if-exists ${PGDATABASE}
	${PG_BINDIR}/createdb ${PGDATABASE}
	./manage.py db upgrade

.PHONY: uwsgi
uwsgi:
	python worker.py &
	uwsgi --ini production.ini

.PHONY: install_live_db
install_live_db:
	${PG_BINDIR}/dropdb --if-exists ${PGDATABASE}
	${PG_BINDIR}/createdb ${PGDATABASE}
	pg_dump --dbname=postgresql://arachnid:devious8ob8@babel/arachnid > mydb.dump
	psql -f mydb.dump


.PHONY: run
run: first-setup-check uwsgi
