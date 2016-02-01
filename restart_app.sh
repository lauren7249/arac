#!/bin/bash
export AC_CONFIG='beta'
. ~/env/bin/activate
pip install -r requirements.txt 
sudo pkill -f track_errors.py
sudo fuser -k 80/tcp
sudo rm true
sudo rm nohup.out
sudo pkill -f worker.py
nohup python worker.py &
sleep 1
sudo ~/env/bin/uwsgi production.ini
sudo nohup ~/env/bin/python track_errors.py & tail -f nohup.out 


