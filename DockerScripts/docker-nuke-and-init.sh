#!/usr/bin/env bash

clear

echo "This script will remove all images from the docker machine and upon"
echo "rebuilding, init the database from scratch."
echo "-----"
echo " "

while true; do
    read -p "Do you wish to proceed?" yn
    case $yn in
        [Yy]* ) docker rm -f $(docker ps -a -q) ; docker rmi $(docker images -q -a); ./docker-build-and-run.sh reset; docker-compose up; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done