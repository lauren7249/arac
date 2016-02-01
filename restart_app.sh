#!/bin/bash
export AC_CONFIG='beta'
. ~/env/bin/activate
pip install -r requirements.txt 
pkill -f track_errors.py
fuser -k 80/tcp
rm true
rm nohup.out
pkill -f worker.py
nohup python worker.py &
sleep 1
~/env/bin/uwsgi production.ini
sleep 2
nohup python track_errors.py & tail -f nohup.out 


