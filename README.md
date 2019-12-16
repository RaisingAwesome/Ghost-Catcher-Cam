# Ghost-Catcher-Cam
A Camera for Ghost Hunting


An up-and-coming project to build a camera that can seek and capture the presense of ghosts and upload it to the cloud.

## Raspberry Pi Setup

### Image

      Install the desktop version:  https://www.raspberrypi.org/downloads/raspbian/
      sudo raspi-config #used to set keyboard, locale, time, enable the camera, SPI, SSH

### Install PiTFT per adafuit.

    https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/easy-install-2
    
    don't worry about the SLD2.0 issue.  You won't use pygame for your GUI.
    Do both calibrations
  
### Hide Mouse Pointer:

      sudo nano /etc/lightdm/lightdm.conf
      <add "xserver-command = X -nocursor" to the bottom of the file>

### Required Software:

#### python3

#### opencv for python3:

      sudo apt-get install python3-opencv
      sudo apt-get install libhdf5-dev
      sudo apt-get install libhdf5-serial-dev
      sudo apt-get install libatlas-base-dev
      sudo apt-get install libjasper-dev 
      sudo apt-get install libqtgui4 
      sudo apt-get install libqt4-test

## Streaming
To screen the entire Raspberry Pi display, this works:

      ffmpeg -f lavfi -i anullsrc -f x11grab -framerate 30 -video_size 480x320 -i :0.0 -f flv -s 480x320 rtmp://a.rtmp.youtube.com/live2/streamkey
