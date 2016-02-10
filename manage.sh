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

# @formatter:off
# Ensure parameter was passed
if [ $# -eq "$NO_ARGS" ] # Script invoked with no command-line args?
then
    echo "Usage: $(basename $0) options (prod_run dev_run test_run )"
    exit "${E_OPTERROR}";
fi
# @formatter:on

# Run in development mode
dev_run() {
    wait_until_is_ready
    first_setup_check
    run_worker
    run_uwsgi
    return $?;
}

prod_run() {
    :
}

# Launch worker and background
run_worker() {
    $(${PYTHON} ./worker.py &)
    return 0;
}

run_uwsgi() {
    $(${UWSGI} --ini production.ini)
    return $?;
}

# Check if the database exists and creates if not
# found.
# TODO: This should be a more rigorous check
first_setup_check() {

    # Return code is 0 only if database exists
    local EXISTS=$(${PG_LIST} | grep "${PG_DB}" -q)

    # For any other return code, create the database
    if [ "${EXISTS}" -neq 0 ]; then
        create_db
    fi
    return 0;
}

reset_db() {
    :
}

# Drop the database
drop_db() {
    $(${PG_BINDIR}/dropdb -h "${PG_HOST}" -U "${PG_USER}" -w --if-exists "${PG_DB}")
    return 0;
}

# Create the default app user and database
# TODO: Handle failures
create_db() {
    { $(${PG_BINDIR}/createuser -h "${PG_HOST}" -U "${PG_USER}" -d -s -w "${PG_DB}"); } || true
    { $(${PG_BINDIR}/createdb -h "${PG_HOST}" -l "${PG_LOCALE}" -w -U "${PG_USER}" "${PG_DB}"); } || true
    $(${PYTHON} ./manage.py db upgrade)
    return 0;
}

# Block until the database is up and answering
wait_until_is_ready() {
    until $(${PG_BINDIR}/pg_isready -h "${PG_HOST}" -U "${PG_USER}"); do
        sleep 5;
    done
    return $?;
}

# Run test scripts
test_run() {
    $(${PYTHON} ./manage.py test)
    return $?;
}

# Entrypoint into script

exit $?