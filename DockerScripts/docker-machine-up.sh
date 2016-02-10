#!/usr/bin/env bash

exit 99
MACHINE=`hostname -s`

docker-machine --debug create  --driver softlayer  --softlayer-api-key 3cee267a0b93e8bd1fb764c3074213602741f0b16642a86f0ced2b76835b0eec \
    --softlayer-cpu "8" --softlayer-disk-size "0" --softlayer-domain "priv.advisorconnect.co" --softlayer-hourly-billing \
    --softlayer-region "dal09" --softlayer-user "james@advisorconnect.co" --softlayer-memory "16384"  ${MACHINE}

eval "$(docker-machine env ${MACHINE})"

IP="$(docker-machine ip ${MACHINE})"

docker info

echo "THE IP OF YOUR REMOTE MACHINE IS ${IP}"

