#!/bin/bash
export DISPLAY=:0.0
cd /home/pi/Ghost-Catcher-Cam
#sudo chmod +777 /dev/sda1
#/usr/bin/python3 /home/pi/Ghost-Catcher-Cam/ghostcv2.py > /home/pi/ghostcatchermain.log 2>&1
/usr/bin/python3 /home/pi/Ghost-Catcher-Cam/ghostcv2.py &

