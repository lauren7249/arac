#!/usr/bin/env bash

docker-compose build

docker-compose run --name prime --rm --service-ports prime $1Add