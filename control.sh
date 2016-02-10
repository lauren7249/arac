#!/usr/bin/env bash
#@formatter:off
#noinspection all
#
# Entrypoint to P200 Application
#
# Copyright 2016, AdvisorConnect, Inc.
# Author: Michael Bishop <michael@advisorconnect.co>
#
#

# Executables
declare -r PG_BINDIR=$(pg_config --bindir)
declare -r PYTHON=$(which python)
declare -r UWSGI=$(which uwsgi)

# Postgres settings
declare -x PG_LOCALE="${LC_ALL:-en_US.utf8}"
declare -x PG_USER="${DB_USER:-postgres}"
declare -x PG_PASS="${DB_PASS}"
declare -x PG_DB="${PG_DB:-arachnid}"
declare -x PG_HOST="${PG_HOST}"

# List of databases command
declare -r PG_LIST="${PG_BINDIR}/psql -h ${PG_HOST} -U ${PG_USER} -l"

# Error messages and conditions
declare -r -i E_MISSING_PARAM=75
declare -r -i E_OPTERROR=85
declare -r -i NO_ARGS=0

# List of functions
declare -a FUNCS

# Bounding box for errors
declare LINE
declare -r -i LENGTH=50
printf -v LINE '%*s' "$LENGTH"

# Run in development mode
dev_run() {
    wait_until_is_ready
    first_setup_check
    run_worker
    run_uwsgi
    return $?;
}

# Run production
# TODO Define
prod_run() {
    :
}

# Run test scripts
test_run() {
    $(${PYTHON} ./manage.py test)
    return $?;
}

# Launch worker and background
run_worker() {
    bg $(${PYTHON} ./worker.py)
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

# TODO Define
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
    until $("${PG_BINDIR}/pg_isready -h ${PG_HOST} -U ${PG_USER}"); do
        sleep 5;
    done
    return $?;
}


#
# Entrypoint into script
#

# Get a list of functions defined in the script and stuff
# into an array
FUNCS=( `compgen -A function` )



# Parse what we've been passed

# Scan the function name array and compare to the
# first command line parameter.  If there's a match,
# call that function name
if [[ " ${FUNCS[@]} " =~ " $1 " ]]
then
    $1;
else
    # Else, echo a usage statement with a list of the
    # function names as valid command options
    echo -e "${LINE// /⁈ }\n"

    echo -e "Usage: $(basename "$0") one of: (${FUNCS[@]} )\n"

    echo -e "${LINE// /⁈ }"
    exit "${E_OPTERROR}";
fi

exit $?
