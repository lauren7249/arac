#!/usr/bin/env bash

declare PG_BINDIR = `pg_config --bindir`
declare PG_USER = ${DB_USER:-'postgres'}
declare PG_PASS = ${DB_PASS}
declare PG_DB = ${PG_DB:-'arachnid'}
declare PG_HOST = ${PG_HOST}
declare PG_LOCALE = ${LC_ALL:-'en_US.utf8'}
declare PYTHON = `which python`
declare UWSGI = `which uwsgi`

function run {
    exit 0
}

function uwsgi {
    ${PYTHON} ./worker.py &
    sleep 2
    ${UWSGI} --ini production.ini
    exit 0
}

function reset-db {
    exit 0
}

function drop-db {
    ${PG_BINDIR}/dropdb -h "${PG_HOST}" -U "${PG_USER}" -w --if-exists "${PG_DB}"
}

# Create the default app user and database
function create-db {
    { ${PG_BINDIR}/createuser -h "${PG_HOST}" -U "${PG_USER}" -d -s -w "${PG_DB}" } || true;
    ${PG_BINDIR}/createdb -h "${PG_HOST}" -l "${PG_LOCALE}" -w -U "${PG_USER}" "${PG_DB}";
    ${PYTHON} ./manage.py db upgrade
}

# Block until the database is up and answering
function wait-until-is-ready {
    until ${PG_BINDIR}/pg_isready -h "${PG_HOST}" -U "${PG_USER}"; do
        sleep 5;
    done
}

# Run test scripts
function test {
    ${PYTHON} ./manage.py test
}

