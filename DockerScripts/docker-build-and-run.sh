#!/usr/bin/env bash
# Think of this as running make <target>
# The prime image as en 'entrypoint' command of make and a default arg of 'test'
# run this command with an argument like run, reset, etc as if this shel script
# where the make command itself.

# Changes in your files should also trigger an auto-rebuild automatically.


docker-compose --file ../docker-compose.yml build --pull

if [$1]
    then
        docker-compose --file ../docker-compose.yml run --name prime --rm --service-ports prime $1
    else
        docker-compose --file ../docker-compose.yml up
fi