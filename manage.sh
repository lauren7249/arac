#!/usr/bin/env bash

#
# Entrypoint to P200 Application
#
# Copyright 2016, AdvisorConnect, Inc.
# Author: Michael Bishop <michael@advisorconnect.co>
#
#

# Executables
declare PG_BINDIR="`pg_config--bindir`"
declare PYTHON="`whichpython`"
declare UWSGI="`whichuwsgi`"

declare PG_LOCALE="${LC_ALL:-'en_US.utf8'}"
declare PG_USER="${DB_USER:-'postgres'}"
declare PG_PASS="${DB_PASS}"
declare PG_DB="${PG_DB:-'arachnid'}"
declare PG_HOST="${PG_HOST}"

# List of databases command
declare PG_LIST="${PG_BINDIR}/psql -h ${PG_HOST} -U ${PG_USER} -l"

# Run in development mode
function dev_run {
    wait_until_is_ready
    first_setup_check
    run_worker
    run_uwsgi
}

function prod_run {
    return 0;
}

# Launch worker and background
function run_worker {

    `${PYTHON} ./worker.py &`
    return 0;
}

function run_uwsgi {
    `${UWSGI} --ini production.ini`
    return $?;
}

# Check if the database exists and creates if not
# found.
# TODO: This should be a more rigorous check
function first_setup_check {

    # Return code is 0 only if database exists
    local EXISTS = `${PG_LIST} | grep "${PG_DB}" -q`

    # For any other return code, create the database
    if [ "${EXISTS}" -neq 0 ]; then
        create_db
    fi
}

function reset_db {
    exit 0;
}

# Drop the database
function drop_db {
    `${PG_BINDIR}/dropdb -h "${PG_HOST}" -U "${PG_USER}" -w --if-exists "${PG_DB}"`;
}

# Create the default app user and database
# TODO: Handle failures
function create_db {
    { `${PG_BINDIR}/createuser -h "${PG_HOST}" -U "${PG_USER}" -d -s -w "${PG_DB}"`
        `${PG_BINDIR}/createdb -h "${PG_HOST}" -l "${PG_LOCALE}" -w -U "${PG_USER}" "${PG_DB}"`
        `${PYTHON} ./manage.py db upgrade` } || true
}

# Block until the database is up and answering
function wait_until_is_ready {
    until `${PG_BINDIR}/pg_isready -h "${PG_HOST}" -U "${PG_USER}"`; do
        sleep 5;
    done;
}

# Run test scripts
function test_app {
    {
        `${PYTHON} ./manage.py test`
    };
}

