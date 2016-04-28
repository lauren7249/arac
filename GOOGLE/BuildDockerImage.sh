#!/usr/bin/env bash

REGISTRY="gcr.io/advisorconnect-1238/"
IMAGE="aconn"
BUILDTYPE="RELEASE"   # oneOF: RELEASE, DEVELOPMENT, TEST, STAGING
VERSION="1.0.33"

BRANCH=`git branch | head -n 1 | cut -c 3-`
# FIXME: Not pulling correct branch (MDB)
# the previous way wasn't getting the right branch for me -lauren
# This is just a label on the image with no implication other than aesthetically
# Will figure out why its not working for you.  These are for future use with
# the deployment system anyway so no worries what it picks for now.
#BRANCH='no-selenium'
COMMIT=`git log  | head -n1 | cut -c 8-16`

echo "Building ${REGISTRY}${IMAGE}:${VERSION}"
echo "BRANCH: $BRANCH"
echo "COMMIT: $COMMIT"

sed -l -e "s/BRANCH--/${BRANCH}/g" -e "s/COMMIT--/${COMMIT}/g" -e "s/ENVIRON--/${BUILDTYPE}/g" Dockerfile > Dockerfile.tmp

gcloud docker push -a
docker --tls build --pull --rm -t ${REGISTRY}${IMAGE}:${VERSION} -f Dockerfile.tmp ..
docker --tls push ${REGISTRY}${IMAGE}:${VERSION}
docker --tls tag  ${REGISTRY}${IMAGE}:${VERSION} ${REGISTRY}${IMAGE}:latest
docker --tls push ${REGISTRY}${IMAGE}:${VERSION}

rm -f Dockerfile.tmp
