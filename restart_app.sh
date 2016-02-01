#!/bin/bash
export AC_CONFIG='beta'
. ~/env/bin/activate
pip install -r requirements.txt 
sudo fuser -k 80/tcp
sudo rm true
sudo rm nohup.out
sudo pkill -f worker.py
nohup python worker.py &
sudo ~/env/bin/uwsgi production.ini
sudo nohup python track_errors.py &>/dev/null

