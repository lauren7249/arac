#!/bin/bash

PG_BINDIR=`pg_config --bindir`
PGDATABASE='arachnid'
HOST='localhost'
PASSWORD='arachnid'


ad=`(psql -h ${HOST} -lqt | cut -d \| -f 1 | grep -w ${PGDATABASE} -q)  && echo $?`
echo ${ad}


if ! [ ${ad} ]; then
    ${PG_BINDIR}/createdb -h ${HOST} -l en_US.utf8 -w ${PGDATABASE}
    echo "Database Created"
fi

. bin/activate
python manage.py db upgrade
