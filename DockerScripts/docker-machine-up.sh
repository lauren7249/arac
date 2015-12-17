#!/usr/bin/env bash

MACHINE=`hostname -s`

docker-machine --debug create  --driver softlayer  --softlayer-api-key 3cee267a0b93e8bd1fb764c3074213602741f0b16642a86f0ced2b76835b0eec \
    --softlayer-cpu "6" --softlayer-disk-size "0" --softlayer-domain "priv.advisorconnect.co" --softlayer-hourly-billing \
    --softlayer-region "wdc01" --softlayer-user "james@advisorconnect.co" --softlayer-memory "16384"  ${MACHINE}

eval "$(docker-machine env ${MACHINE})"

docker info


echo "docker-build-and-run <make command>     <----- build and run"
