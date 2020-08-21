# Ghost-Catcher-Cam
A Camera for Ghost Hunting


An up-and-coming project to build a camera that can seek and capture the presense of ghosts and upload it to the cloud.

## Raspberry Pi Setup for the Ghost-Catcher-Cam

### 1.  Create the Raspian Image

a.  Install the desktop version of Raspian:  https://www.raspberrypi.org/downloads/raspbian/

+ You'll need to hook your Raspberry pi to a mouse, keyboard, and monitor with an HDMI cord.

+ With the desktop wizard, follow the prompts to config the desktop and run updates.  Choose not to reboot.  Click on the terminal icon.

b.  Open a terminal and type the following to enable the camera and SSH interface
      
      sudo raspi-config #enable the camera, SSH
      
c.  Get rid of the Trash can.  Click the "Start" button, then Preferences-->Appearance Settings-->Wastebasket

### 2.  Install PiTFT Display Kernal per Adafuit:

    https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/easy-install-2
+ Options to select when prompted:

      4. PiTFT 3.5" resistive touch (320x480)

      1. 90 degrees (landscape)

      Would you like the console to appear on the PiTFT display? [y/n] n

      Would you like the HDMI display to mirror to the PiTFT display? [y/n] y


+ After the reboot, you should be done with the setup.  Don't worry about the SLD2.0 issue it talks about in PyGame tips.  You won't use PyGame for your GUI.  Also, You shouldn't need to calibrate, but can follow there instructions if you find it off.
  
### 3.  Hide the Mouse Pointer:

For a touch screen GUI, a mouse pointer popping up looks goofy.  So, to get rid of it use the text editor nano to open the following file and then put the second line under the commented #xserver-command=X line in the [Seat:*] section.  The -s 0 dpms will prevent the screen from going blank if not touched for a while.

      sudo nano /etc/lightdm/lightdm.conf
      xserver-command=X -nocursor -s 0 dpms

### 4.  Install the Required Software:

#### a.  Python3
Ensure you have python3 installed by typing python3.  You should have it already installed.  Type exit() to exit out of it.  If you don't have it, Google how to install python on Raspberry pi X, where X is your version.

#### b.  PyUserInput  
Install the package that allows you to move the mouse cursor.  This is needed to hide the mouse when streaming.  Even though the above section hides the mouse pointer on the screen, its magically still there when streaming.  So, we move it with code to the lower right out of view.
      
      sudo pip3 install PyUserInput #hide the mouse while streaming

#### c.  OpenCV for Python3:

      sudo apt-get install python3-opencv #takes a while, its bigger than 250M
           
### 5.  Clone this Repository:
a.  From the terminal, paste the following:

      cd ~
      git clone https://github.com/RaisingAwesome/Ghost-Catcher-Cam
      cd Ghost-Catcher-Cam
      sudo chmod +777 runner.sh
      ./runner.sh #to run it

b.  Copy the bootup splash screen.  You can change it by making a .png image with dimensions 480x320.  This post tells you how to get rid of the stuff at the bottom of the screen:  https://www.thedigitalpictureframe.com/customize-your-raspberry-pi-splash-screen-raspbian-stretch-april-2019-version/.  It is possible that it boots so fast that you don't get to see it.  In turn, you may want to set this as the Raspberry Pi Desktop background instead.   

      cd Ghost-Catcher-Cam
      sudo cp splash.png /usr/share/plymouth/themes/pix/
      sudo reboot

c.  Hide your Taskbar.  To do this, open a terminal and edit the LXDE-pi/autostart file as shown here:

      sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
      
      #comment out the line with @lxpanel --profile LXDE

### 6.  Accelerometer
a.  The 3-axis magnetometer:  https://www.amazon.com/gp/product/B008V9S64E/ref=ppx_yo_dt_b_asin_title_o08_s00?ie=UTF8&psc=1

b.  It is used for the "scan" mini game that requires turning and camera and holding it very still in order to hear audio.

c.  Clone the accelerometer repo:

      git clone https://github.com/RigacciOrg/py-qmc5883l.git
      cd py-qmc58831
      sudo python3 setup.py install
      cd ..
      rm -r py-qmc58831 #if you want to free up space


### 7.  Make it Autoboot
You first have to set permissions on the runner file:

      cd ~/Ghost-Catcher-Cam
      chmod +777 runner.sh
      
+Then, set a Crontab entry so it runs at startup:

      crontab -e

+Type the following at the bottom of the page:

      @reboot sleep 0 && /home/pi/Ghost-Catcher-Cam/runner.sh &  #increase the sleep zero if it doesn't run to give it time to boot up more dependancies.  The sleep parameter is in seconds.
      
### Extra Info:
For info, to stream the entire Raspberry Pi display, this work:

      ffmpeg -f lavfi -i anullsrc -f x11grab -framerate 30 -video_size 720x480 -i :0.0 -f flv -s 720x480 rtmp://a.rtmp.youtube.com/live2/streamkey

This approach is used by the ghostcv2.py program.

If you ever need a time you want to kill the backlight to save battery, you can do this:

      sudo sh -c 'echo "0" > /sys/class/backlight/soc\:backlight/brightness'    

To eliminate the lightening bolt shown when the board is underpowered:
      sudo nano /boot/config.txt
      Add this text to the bottom of the file
      Disable under-voltage warning
      avoid_warnings=1  
      
Sound troubleshooting:
      After updating, you might run into an error that amixer is unable to find a simple control
      First do a sudo raspi-config-->Advanced Options-->Audio-->Headphones
      Type: amixer scontrols
      This will give you the name of the sound card.  Edit ghostcv2.py on the 3 lines that contain 
      amixer to enxure it is calling the sound card correctly.
