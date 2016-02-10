#!/usr/bin/env bash

# Executables
declare PG_BINDIR = `pg_config --bindir`
declare PYTHON = `which python`
declare UWSGI = `which uwsgi`

declare PG_LOCALE = ${LC_ALL:-'en_US.utf8'}
declare PG_USER = ${DB_USER:-'postgres'}
declare PG_PASS = ${DB_PASS}
declare PG_DB = ${PG_DB:-'arachnid'}
declare PG_HOST = ${PG_HOST}

# List of databases command
declare PG_LIST = "${PG_BINDIR}/psql -h "${PG_HOST}" -U "${PG_USER}" -l"


function run {
    return 0;
}

function uwsgi {
    worker
    sleep 2
    ${UWSGI} --ini production.ini
    return;
}

# Launch worker and background
function worker {
    {
        ${PYTHON} ./worker.py &
    }
    return;
}

# Check if the database exists and creates if not
# found.
# TODO: This should be a more rigorous check
function first-setup-check {

    # Return code is 0 only if database exists
    local EXISTS = `${PG_LIST} | grep "${PG_DB}" -q`

    # For any other return code, create the database
    if [ "${EXISTS}" -neq 0 ]; then
        create-db
    fi
}

function reset-db {
    exit 0;
}

function drop-db {
    ${PG_BINDIR}/dropdb -h "${PG_HOST}" -U "${PG_USER}" -w --if-exists "${PG_DB}";
}

# Create the default app user and database
function create-db {
    { ${PG_BINDIR}/createuser -h "${PG_HOST}" -U "${PG_USER}" -d -s -w "${PG_DB}"
        ${PG_BINDIR}/createdb -h "${PG_HOST}" -l "${PG_LOCALE}" -w -U "${PG_USER}" "${PG_DB}"
        ${PYTHON} ./manage.py db upgrade } || true
}

# Block until the database is up and answering
function wait-until-is-ready {
    until ${PG_BINDIR}/pg_isready -h "${PG_HOST}" -U "${PG_USER}"; do
        sleep 5;
    done;
}

# Run test scripts
function test {
    {
        ${PYTHON} ./manage.py test
    };
}

