#!/bin/bash
export AC_CONFIG='beta'
. ~/env/bin/activate
pip install -r requirements.txt 
sudo pkill -f track_errors.py
sudo fuser -k 80/tcp
sudo rm true
sudo rm nohup.out
sudo pkill -f worker.py
sudo nohup python worker.py &
sleep 1
sudo ~/env/bin/uwsgi production.ini
# sleep 2
# sudo nohup python track_errors.py & sudo tail -f nohup.out 


