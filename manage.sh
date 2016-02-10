#!/usr/bin/env bash

#
# Entrypoint to P200 Application
#
# Copyright 2016, AdvisorConnect, Inc.
# Author: Michael Bishop <michael@advisorconnect.co>
#
#

# Executables
# @formatter:off
declare -r PG_BINDIR=$(pg_config --bindir)
declare -r PYTHON=$(which python)
declare -r UWSGI=$(which uwsgi)
# @formatter:on

# Postgres settings
declare -x PG_LOCALE="${LC_ALL:-'en_US.utf8'}"
declare -x PG_USER="${DB_USER:-'postgres'}"
declare -x PG_PASS="${DB_PASS}"
declare -x PG_DB="${PG_DB:-'arachnid'}"
declare -x PG_HOST="${PG_HOST}"

# List of databases command
declare -r PG_LIST="${PG_BINDIR}/psql -h ${PG_HOST} -U ${PG_USER} -l"

# Error messages and conditions
declare -r -i E_MISSING_PARAM=75
declare -r -i E_OPTERROR=85
declare -r -i NO_ARGS=0


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
    $(${PYTHON} ./worker.py &)
    return 0;
}

function run_uwsgi {
    $(${UWSGI} --ini production.ini)
    return $?;
}

# Check if the database exists and creates if not
# found.
# TODO: This should be a more rigorous check
function first_setup_check {

    # Return code is 0 only if database exists
    local EXISTS=$(${PG_LIST} | grep "${PG_DB}" -q)

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
    $(${PG_BINDIR}/dropdb -h "${PG_HOST}" -U "${PG_USER}" -w --if-exists "${PG_DB}");
}

# Create the default app user and database
# TODO: Handle failures
function create_db {
    { $(${PG_BINDIR}/createuser -h "${PG_HOST}" -U "${PG_USER}" -d -s -w "${PG_DB}") } || true
    { $(${PG_BINDIR}/createdb -h "${PG_HOST}" -l "${PG_LOCALE}" -w -U "${PG_USER}" "${PG_DB}") } || true
    $(${PYTHON} ./manage.py db upgrade)
}

# Block until the database is up and answering
function wait_until_is_ready {
    until $(${PG_BINDIR}/pg_isready -h "${PG_HOST}" -U "${PG_USER}"); do
        sleep 5;
    done;
}

# Run test scripts
function test_run {
    $(${PYTHON} ./manage.py test)
}

# Entrypoint into script

# Ensure parameter was passed
if [ $# -eq "$NO_ARGS" ] # Script invoked with no command-line args?
then
    echo "Usage: `basename$0` options (prod_run dev_run test_run )"
    exit "${E_OPTERROR}"


fi

exit $?