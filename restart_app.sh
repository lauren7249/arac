#!/bin/bash
export AC_CONFIG='beta'
. ./vars.sh
. ~/env/bin/activate
#pip install -r requirements.txt 
sudo pkill -f track_errors.py
sudo fuser -k 80/tcp
sudo rm -f true 
sudo rm nohup.out
sleep 1
sudo ~/env/bin/uwsgi production.ini
sudo pkill -f worker.py
nohup python worker.py & 
sleep 5
sudo nohup python track_errors.py & 


