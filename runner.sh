#!/bin/bash
DISPLAY=:0.0 /usr/bin/xhost +local:pi
cd /home/pi/RaspberryPiRepositories/Ghost-Catcher-Cam
/usr/bin/python3 /home/pi/RaspberryPiRepositories/Ghost-Catcher-Cam/ghostcv2.py
