# Ghost-Catcher-Cam
A Camera for Ghost Hunting


An up-and-coming project to build a camera that can seek and capture the presense of ghosts while streaming to the cloud or USB storage.

## Raspberry Pi Setup for the Ghost-Catcher-Cam

### 1.  Create the Raspian Image

a.  Install the desktop version of Raspian:  https://www.raspberrypi.org/downloads/raspbian/

+ You'll need to hook your Raspberry pi to a mouse, keyboard, and monitor with an HDMI cord.

+ With the desktop wizard, follow the prompts to config the desktop and run updates.  Choose not to reboot.  Click on the terminal icon.

b.  Open a terminal and type the following to enable the camera and SSH interface (or do this from the Desktop Menu) and the Headphone Jack
      
      sudo raspi-config #enable the camera, SSH under the interfaces option 
      #System Options-->Audio-->Headphones    
      
      
c.  Get rid of the Trash can and mounted disks.  Click the "Start" button, then Preferences-->Appearance Settings-->Wastebasket/Mounted Disks

### 2.  Install PiTFT Display Kernal per Adafuit:

    https://learn.adafruit.com/adafruit-pitft-3-dot-5-touch-screen-for-raspberry-pi/easy-install-2
    
    sudo python3 adafruit-pitft.py #don't use the parameters because it doesn't default to the options you need
    
+ Options to select when prompted:

      4. PiTFT 3.5" resistive touch (320x480)

      1. 90 degrees (landscape)

      Would you like the console to appear on the PiTFT display? [y/n] n

      Would you like the HDMI display to mirror to the PiTFT display? [y/n] y


+ After the reboot, you should be done with the setup.  Don't worry about the SLD2.0 issue it talks about in PyGame tips.  You won't use PyGame for your GUI.  Also, You shouldn't need to calibrate, but can follow there instructions if you find it off.
  
### 2a.  Prepare an Uctronics Display:
+ This is an alternate, more afordable display with better specifications.  The only downside is that it shows a bootup splash screen that is annoying.

     https://github.com/UCTRONICS/UCTRONICS_HSLCD35
     
     wget https://raw.githubusercontent.com/UCTRONICS/UCTRONICS_LCD35_RPI/master/install
     
+ After you do the wget, follow their instructions.  Their is a chance that your Raspberry Pi OS image is not updated on their git hub.  You will know because there will be an early error message that the "cp" failed.  If that happens find their newest driver under the Raspbian/usr directory of the package and copy it as such:

     cp /Raspbian/usr/5.4.79-v7l+/uctronics-hslcd35-overlay.dtb /boot/overlays/uctronics-hslcd35.dtbo
     
     sudo ./UCTRONICS_HSLCD35/Raspbian/UCTRONICS_HSLCD35_SHOW

+ After you have the screen working, use the desktop Preferences->Display settings to set the display to 780 and checkmark overscan.  This will allow the display to scale the screen and the images fit correctly.  The overscan will eliminate a black bar all the way around the image in 780 mode.  If it doesn't work, in the terminal do a sudo rasp-config and find the overscan setting and turn it on there.

### 3.  Hide the Mouse Pointer:

For a touch screen GUI, a mouse pointer popping up looks goofy.  So, to get rid of it use the text editor nano to open the following file and then put the second line under the commented #xserver-command=X line in the [Seat:*] section.  Using -s 0 dpms will prevent the screen from going blank if not touched for a while.  Using -s 5 dpms shuts it off after 5 minutes.

      sudo nano /etc/lightdm/lightdm.conf
      xserver-command=X -nocursor -s 5 dpms

### 4.  Install the Required Software:

#### a.  Python3
Ensure you have python3 installed by typing python3.  You should have it already installed.  Type exit() to exit out of it.  If you don't have it, Google how to install python on Raspberry pi X, where X is your version.

#### b.  PyUserInput  
Install the package that allows you to move the mouse cursor.  This is needed to hide the mouse when streaming.  Even though the above section hides the mouse pointer on the screen, its magically still there when streaming.  So, we move it with code to the lower right out of view.
      
      sudo pip3 install PyUserInput #hide the mouse while streaming

#### c.  OpenCV for Python3:
      sudo apt install python3-opencv
      
#### d.  espeak (used to play the words.txt file)
      sudo apt install espeak -y
      
#### e.  SOX (used to play output from espeak:
      sudo apt install sox
                
### 5.  Clone this Repository and Setup the Environment:
a.  From the terminal, paste the following:

      cd ~
      git clone https://github.com/RaisingAwesome/Ghost-Catcher-Cam
      cd Ghost-Catcher-Cam
      sudo chmod +777 runner.sh
      ./runner.sh #to run it

b.  Copy the bootup splash screen.  You can change it by making a .png image with dimensions 480x320.  This post tells you how to get rid of the stuff at the bottom of the screen:  https://www.thedigitalpictureframe.com/customize-your-raspberry-pi-splash-screen-raspbian-stretch-april-2019-version/.  It is possible that it boots so fast that you don't get to see it.  In turn, you may want to set this as the Raspberry Pi Desktop background instead.   

      cd Ghost-Catcher-Cam
      sudo cp images/splash.png /usr/share/plymouth/themes/pix/
      sudo reboot

c.  Hide your Taskbar.  To do this, open a terminal and edit the LXDE-pi/autostart file as shown here:

      sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
      
      #comment out the line with @lxpanel --profile LXDE
d.  Set your desktop background

      nano ~/.config/pcmanfm/LXDE-pi/desktop-items-0.conf
      #set wallpaper=/home/pi/Ghost-Catcher-Cam/images/splash.png

e.  Make a RAMDisk.  

The ramdisk is used to pipe a file into ffmpeg named 'stop'.  If the file has the letter q in it, it simulates pressing q with ffmpeg running in the command prompt telling it to quit.  Very ingenius way of getting ffmpet to stop without killing the process the hard way.

Do this in the terminal:

    mkdir /home/pi/Ghost-Catcher-Cam/ramdisk
    sudo nano /etc/fstab

Paste this at the bottom and save with CTRL x:

    myramdisk  /home/pi/Ghost-Catcher-Cam/ramdisk  tmpfs  defaults,size=64k,x-gvfs-show  0  0

f.  Set up for USB Storage

First, make a directory:  mkdir /home/pi/usbdrv

Then get your UUID for the drive with this command:

     ls -l /dev/disk/by-uuid | grep sda1

then do sudo nano /etc/fstab and add the following line REPLACING YOUR UUID from above:

     UUID=6D80-1752 /home/pi/usbdrv vfat defaults,auto,users,rw,nofail,umask=000 0 0

g.  Set GPIO 22 to output high on boot to latch in the power (if have the latching motherboard I designed)
     
     sudo nano /boot/config.txt
     #add the line 
     gpio=22=op,dh
     gpio=23,op,dh
     
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
      chmod +777 runner.sh #this is the main runner of the python script
      chmod +777 checker.sh #this will ensure it boots successfully and will reboot if not
      
Then, set a Crontab entry so it runs at startup:

      crontab -e

Type the following at the bottom of the page:

      @reboot sleep 10 && /home/pi/Ghost-Catcher-Cam/runner.sh &  #increase the sleep zero if it doesn't run to give it time to boot up more dependancies.  The sleep parameter is in seconds.
      @reboot sleep 30 && /home/pi/Ghost-Catcher-Cam/checker.sh & #this will reboot if python isn't running after 30 seconds.

### 8: Troubleshooting
Sound troubleshooting:
      After updating, you might run into an error that amixer is unable to find a simple control

      1. First do a sudo raspi-config-->Advanced Options-->Audio-->Headphones
      2. Type: amixer scontrols
      3. This will give you the name of the sound card.  Edit ghostcv2.py on the 3 lines that contain 
      amixer to ensure it is calling the sound card correctly.

Fixing Boot Issues:
+ If you get it working, it's best to never do an upgrade no matter how bad you feel like doing it.
+ Often, it is the "import cv2" that is failing.  It has been known to either cause a Segmentation Fault or some .o file problem.
+ You can look for errors on bootup with:  

      journalctl -b
      dmesg
+ If you get an error message such as /usr/lib/libxxx, you can find the package name with

      apt list --installed
+ Some things to try, but have never worked:

      sudo apt-get reinstall coreutils
      sudo apt-get reinstall python3-opencv2
      #also, reinstall the display driver from adafruit

+ Sometimes you will get this:

      ImportError: /usr/lib/libgdal.so.20: undefined symbol: _JN11OGRSFDriver16CreateDataSourceEPKcPPc
      #do this
      sudo apt-get reinstall libgdal20

### 9:  Good to Know Stuff
+ Redirecting Command Line Output:

      When using os.system in Python, you typically want to hide all console messages by sending them to null.  
      
      You can do so with the following at the end of the command line string:
      
      2>/dev/null
      
+     Measure Temp:  vcgencmd measure_temp

+     apt list --installed #shows installed packages

+     For info, to stream the entire Raspberry Pi display, this work:

      ffmpeg -f pulse -i alsa_output.platform-bcm2835_audio.analog-stereo.monitor -f x11grab -framerate 30 -video_size 720x480 -i :0.0 -f flv -b:v 1024K -framerate 30 -s 854x480 rtmp://a.rtmp.youtube.com/live2/streamkey
      
      The alsa_output was found with ffmpeg -sources pulse

This approach is used by the ghostcv2.py program.
+     If you ever need a time you want to kill the backlight to save battery, you can do this:

      sudo sh -c 'echo "0" > /sys/class/backlight/soc\:backlight/brightness'    
      
