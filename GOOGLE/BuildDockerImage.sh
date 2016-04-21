#!/usr/bin/env bash

REGISTRY="gcr.io/advisorconnect-1238/"
IMAGE="aconn"
VERSION="1.0.9"

BRANCH=`git branch | head -n 1 | cut -c 3-`
COMMIT=`git log  | head -n1 | cut -c 8-16`

echo "Building ${REGISTRY}${IMAGE}:${VERSION}"
echo "BRANCH: $BRANCH"
echo "COMMIT: $COMMIT"

sed -l -e "s/BRANCH--/${BRANCH}/g" -e "s/COMMIT--/${COMMIT}/g" Dockerfile > Dockerfile.tmp

gcloud docker push -a
docker --tls build --pull --rm -t ${REGISTRY}${IMAGE}:${VERSION} -f Dockerfile.tmp ..
docker --tls push ${REGISTRY}${IMAGE}:${VERSION}
docker --tls tag  ${REGISTRY}${IMAGE}:${VERSION} ${REGISTRY}${IMAGE}:latest
docker --tls push ${REGISTRY}${IMAGE}:${VERSION}

rm -f Dockerfile.tmp