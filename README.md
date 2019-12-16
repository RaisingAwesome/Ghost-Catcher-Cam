# Ghost-Catcher-Cam
A Camera for Ghost Hunting


An up-and-coming project to build a camera that can seek and capture the presense of ghosts and upload it to the cloud.

## Raspberry Pi Setup

### Image

1.  Install the desktop version of Raspian:  https://www.raspberrypi.org/downloads/raspbian/

      You'll need to hook your Raspberry pi to a mouse, keyboard, and monitor with an HDMI chord.
      
      With the desktop wizard, follow the prompts to config the desktop and run updates.  Choose not to reboot.  Click on the terminal icon.

2.  Open a terminal and type the following to enable the camera and SSH interface
      
      sudo raspi-config #enable the camera, SSH

### Install PiTFT per adafuit.

    https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/easy-install-2
Options to select when prompted:

      4. PiTFT 3.5" resistive touch (320x480)

      1. 90 degrees (landscape)

      Would you like the console to appear on the PiTFT display? [y/n] n

      Would you like the HDMI display to mirror to the PiTFT display? [y/n] y



    don't worry about the SLD2.0 issue.  You won't use pygame for your GUI.
    You shouldn't need to calibrate, but can if you find it off.
  
### Hide Mouse Pointer:

For a touch screen GUI, a mouse pointer popping up looks goofy.  So, to get rid of it use the text editor nano to open the following file and then put the second line under the commented #xserver-command=X line in the [Seat:*] section.

      sudo nano /etc/lightdm/lightdm.conf
      xserver-command=X -nocursor      
      
      

### Install the Required Software:

#### 1.  python3
Ensure you have python3 installed by typing python3.  You should have it already installed.  Type exit() to exit out of it.  If you don't have it, Google how to install python on Raspberry pi X, where X is your version.

#### 2.  PyUserInput  
Install the package that allows you to move the mouse cursor.  This is needed to hide the mouse when streaming.  Even though the above section hides the mouse pointer on the screen, its magically still there when streaming.  So, we move it with code to the lower right out of view.
      
      sudo pip3 install PyUserInput #hide the mouse while streaming

#### OpenCV for python3:

      sudo apt-get install python3-opencv #takes a while, its bigger than 250M
      sudo apt-get install libhdf5-dev
      sudo apt-get install libhdf5-serial-dev
      sudo apt-get install libatlas-base-dev
      sudo apt-get install libjasper-dev 
      sudo apt-get install libqtgui4 
      sudo apt-get install libqt4-test
           
## Clone this repository
1.  From the terminal, paste the following:
      cd ~
      git clone https://github.com/RaisingAwesome/Ghost-Catcher-Cam

2.  Copy a new splash screen, make a .png image with dimensions 420x380 and type the following:
      cd Ghost-Catcher-Cam
      sudo cp splash.png /usr/share/plymouth/themes/pix/

## Streaming Tip
For info, to stream the entire Raspberry Pi display, this work:

      ffmpeg -f lavfi -i anullsrc -f x11grab -framerate 30 -video_size 480x320 -i :0.0 -f flv -s 480x320 rtmp://a.rtmp.youtube.com/live2/streamkey

This approach is used by the ghostcv2.py program.
      
      
