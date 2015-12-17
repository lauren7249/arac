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
        clear
        echo "Would you like to run in the foreground?  No will launch in daemon/background mode."
        echo "----"
        echo ""
        while true; do
            read -p "Daemonize?" yn
            case $yn in
                [Yy]* ) docker-compose --file ../docker-compose.yml -d up; exit;;
                [Nn]* ) docker-compose --file ../docker-compose.yml up; exit;;
                * ) echo "Please answer yes or no.";;
            esac
        done
fi