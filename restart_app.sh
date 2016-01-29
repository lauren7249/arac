#!/bin/bash
export AC_CONFIG='beta'
. ~/env/bin/activate
cd ~/prime
sudo fuser -k 80/tcp
sudo ~/env/bin/uwsgi production.ini