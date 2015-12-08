#!/usr/bin/env bash
#
#  If you aren't Michael, you probably will never need to run this
#

echo "Make sure you're connected to a local or remote Docker host, this build takes a long time!"

docker build --rm --tag acmichael/python2-onbuild:latest

docker login -u acmichael -p d0gs9900 -e michael@advisorconnect.co

docker push acmichael/python2-onbuild:latest