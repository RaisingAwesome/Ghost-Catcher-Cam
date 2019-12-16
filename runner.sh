#!/bin/bash
DISPLAY=:0.0 /usr/bin/xhost +local:tp
cd /home/tp/RaspberryPiRepositories/Ghost-Catcher-Cam
/usr/bin/python3 /home/tp/RaspberryPiRepositories/Ghost-Catcher-Cam/ghostcv2.py
