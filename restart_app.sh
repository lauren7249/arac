#!/bin/bash
export AC_CONFIG='beta'
. ~/env/bin/activate
sudo fuser -k 80/tcp
sleep 1
sudo ~/env/bin/uwsgi production.ini