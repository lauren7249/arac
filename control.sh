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
PATH="$PATH:$PG_BINDIR"

# Postgres settings
declare -x PG_LOCALE="${LC_ALL:-en_US.utf8}"
declare -x PG_USER="${DB_USER:-postgres}"
declare -x PG_PASS="${DB_PASS}"
declare -x PG_DB="${PG_DB:-arachnid}"
declare -x PG_HOST="${PG_HOST}"

# List of databases command
declare -r PG_LIST="${PG_BINDIR}/psql -h ${PG_HOST} -U ${PG_USER} -l "

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
    { coproc worker { $(${PYTHON} ./worker.py) ; }>&3; } 3>&1
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
    # In all other cases there is a null return code

    $PG_LIST  # Debug statement / Sanity Check

    local EXISTS_CMD="${PG_LIST} | grep "${PG_DB}" -q"

    local CODE=`eval $PG_LIST`
    echo "RETCODE: $CODE"

    if [ -n "${CODE}" ]; then
        echo "${PG_DB} Exists"
        return 0;
    else
        echo "${PG_DB} does not yet exist.  Creating."
        create_db;
    fi
    return 0;
}

# TODO Define
reset_db() {
    :
}

# Drop the database
drop_db() {
    local DROP_CMD="${PG_BINDIR}/dropdb -h ${PG_HOST} -U ${PG_USER} -w --if-exists ${PG_DB}"
    local RC=$(eval ${DROP_CMD})
    return $RC;
}

# Create the default app user and database
# TODO: Handle failures
create_db() {
    local CREATE_USR_CMD="${PG_BINDIR}/createuser -h ${PG_HOST} -U ${PG_USER} -d -s -w ${PG_DB}"
    local CREATE_DB_CMD="${PG_BINDIR}/createdb -h ${PG_HOST} -l ${PG_LOCALE} -w -U ${PG_USER} ${PG_DB}"
    local UPGRADE_DB_CMD="${PYTHON} ./manage.py db upgrade"

    eval $CREATE_USR_CMD
    eval $CREATE_DB_CMD
    RC=$(eval $UPGRADE_DB_CMD)

    return $RC;
}

# Block until the database is up and answering
wait_until_is_ready() {
    local IS_READY_TEST="${PG_BINDIR}/pg_isready -h ${PG_HOST} -U ${PG_USER} "
    until $IS_READY_TEST; do
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
