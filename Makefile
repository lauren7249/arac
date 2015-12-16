PGDATABASE ?= arachnid
PG_BINDIR  := $(shell pg_config --bindir)
pg         := ${PG_BINDIR}/psql -d ${PGDATABASE}

.PHONY: create-db
create-db:
    ${PG_BINDIR}/createuser -d -s -U postgres -w  ${PRMIE_DB_USER}
	${PG_BINDIR}/createdb -l en_US.utf8 -w -U postgres ${PGDATABASE}
	./manage.py db upgrade

.PHONY: generate-fake
generate-fake:
	./manage.py generate_fake

.PHONY: drop-db
drop-db:
	${PG_BINDIR}/dropdb -U postgres -w --if-exists ${PGDATABASE}

.PHONY: reset
reset: drop-db create-db

.PHONY: test
test:
	./manage.py test
