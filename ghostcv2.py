import cv2
import os
from pymouse import PyMouse
from picamera.array import PiRGBArray
from picamera import PiCamera
import time

os.putenv('SDL_VIDEODRIVER','fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
SCREEN_MENU=0
MOUSE_IGNORE=False
WINDOW_NAME="mywindow"

def HideMouse():
    global MOUSE_IGNORE
    # click the mouse out of the view.  for some reason, even though I hide it in the operating system, it shows when streaming.
    MOUSE_IGNORE=True #don't want to register a real click that the logic will catch.  6 will be caught and ignored by the handler
    m = PyMouse()
    m.click(720, 480, 1)
    k=cv2.waitKey(10) # allow time to process without problems
    MOUSE_IGNORE=False
    
def StreamIt():
    # Reference - http://www.pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/
    
    global current_screen, WINDOW_NAME, img, camera, rawCapture, SCREEN_MENU

    # allow the camera to warmup
    time.sleep(0.1)
    os.system("sudo chmod +777 /home/pi/Ghost-Catcher-Cam/stop")
    os.system("sudo rm /home/pi/Ghost-Catcher-Cam/stop") #this will let us stop the stream

    os.system("sudo touch /home/pi/Ghost-Catcher-Cam/stop") #by creating an empty file named stop.  Once it has a q in it, ffmpeg will get the q and then stop
    os.system("sudo chmod +777 /home/pi/Ghost-Catcher-Cam/stop")
    
    # Get the current Youtube stream key
    streamkeyfile=open("streamkey.cfg","r")
    streamkey=streamkeyfile.read()
    # just in case there is some sloppy hand typing going on, we'll strip off any white space
    streamkey.rstrip("\n")
    streamkey.rstrip("\r")
    streamkeyfile.close()
    
    # Start streaming with ffmpeg
    streamkey="</home/pi/Ghost-Catcher-Cam/stop /usr/bin/ffmpeg -f lavfi -i anullsrc -f x11grab -framerate 30 -video_size 720x480 -i :0.0 -f flv -s 720x480 rtmp://a.rtmp.youtube.com/live2/" + streamkey + " >/dev/null 2>>Capture.log &"
    os.system(streamkey)
    
    HideMouse()
    
    # capture frames from the camera
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    	# grab the raw NumPy array representing the image, then initialize the timestamp
    	# and occupied/unoccupied text
    	img = frame.array
    	# img=cv2.resize(img, (720,480),interpolation = cv2.INTER_AREA)

    	img = cv2.putText(img, 'Raising Awesome!', (67, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
        # show the frame
    	cv2.imshow(WINDOW_NAME, img)
    	key = cv2.waitKey(1)

    	# clear the stream in preparation for the next frame
    	rawCapture.truncate(0)

    	# if the `q` key was pressed, break from the loop
    	if current_screen==SCREEN_MENU:
    	    os.system("echo 'q' >stop") #this simulates a keypress of the letter q which stops ffmpeg.  it's genius
    	    # idea came from https://stackoverflow.com/questions/9722624/how-to-stop-ffmpeg-remotely
    	    break
    	
def ConfigYouTube():
    global img, WINDOW_NAME
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm2.png',1)
    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(1)
    my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Attach Keyboard and Enter YouTube Stream Key:' --entry --width=300 --height=200 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/temp_streamkey.cfg")
    if my_result==0:
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        # do the copying
        os.system("cp /home/pi/Ghost-Catcher-Cam/temp_streamkey.cfg /home/pi/Ghost-Catcher-Cam/streamkey.cfg")
        my_result=os.system("DISPLAY=:0.0 zenity --title='WiFi Config' --info='Stream Set, Good Job.' --width=100 --height=100")
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)

def UpdateWiFi():
    # sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
    the_file=open("/home/pi/Ghost-Catcher-Cam/temp_wifi_ssid.cfg","r")
    ssid=the_file.read()
    ssid=ssid.rstrip()
    the_file.close
    the_file=open("/home/pi/Ghost-Catcher-Cam/temp_wifi_password.cfg","r")
    pwd=the_file.read()
    pwd=pwd.rstrip()
    the_file.close()

    os.system("echo \"ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\\nupdate_config=1\\ncountry=US\\n\\nnetwork={\\nssid=\\\"" + ssid + "\\\"\\npsk=\\\"" + pwd + "\\\"\\nkey_mgmt=WPA-PSK\\n}\" > /home/pi/Ghost-Catcher-Cam/tempwifi.cfg")
    os.system("sudo cp /home/pi/Ghost-Catcher-Cam/tempwifi.cfg /etc/wpa_supplicant/wpa_supplicant.conf")
    
def IsCanceled(the_file):
    myfile=open(the_file,"r")
    the_value=myfile.read()
    myfile.close()
    if len(the_value)<5:
        return True
    else:
        return False
        
def ConfigWiFi():
    global img, WINDOW_NAME
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm2.png',1)
    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(1)
    my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Attach Keyboard and Enter SSID:' --entry --width=300 --height=200 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/temp_wifi_ssid.cfg")
    if not IsCanceled("/home/pi/Ghost-Catcher-Cam/temp_wifi_ssid.cfg"):
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Enter Password:' --entry --hide-text --width=300 --height=200 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/temp_wifi_password.cfg")    
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        if not IsCanceled("/home/pi/Ghost-Catcher-Cam/temp_wifi_password.cfg"):
            # do the copying
            UpdateWiFi()
            my_result=os.system("DISPLAY=:0.0 zenity --title='WiFi Config' --info='WiFi Reset!  Tap to Reboot' --width=100 --height=100")
            img = cv2.imread('/home/pi/Ghost-Catcher-Cam/rebooting.png',1)
            cv2.imshow(WINDOW_NAME,img)
            k=cv2.waitKey(2000)
            cv2.destroyAllWindows()
            os.system("( sleep 1 ; sudo reboot )")
            exit()
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
    k=cv2.waitKey(1)
    
def MouseHandler(event, x, y, flags, param):
    #Handle screen taps based on what screen is showing
    global user_tapped_exit, current_screen, img,WINDOW_NAME, MOUSE_IGNORE
    
    if MOUSE_IGNORE:
        return

    if event==cv2.EVENT_LBUTTONUP:
        if current_screen==5:
            current_screen=SCREEN_MENU
            img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
        elif (x>82 and x<252 and y>90 and y<217): #handle go live tap
            current_screen=4
            img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm.png',1)
            img = cv2.putText(img, 'Start Streaming!?', (67, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
            img = cv2.putText(img, 'Start Streaming!?', (67, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)
        elif (x>465 and x<627 and y>90 and y<217):
            if current_screen==SCREEN_MENU: #Handle tapped power button
                current_screen=1
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm.png',1)
                img = cv2.putText(img, 'Turn Off Camera?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
                img = cv2.putText(img, 'Turn Off Camera?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)  
            elif current_screen==1:
                user_tapped_exit=True
            else:
                current_screen=SCREEN_MENU
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
        elif (x>82 and x<252 and y>294 and y<420):
            if current_screen==SCREEN_MENU: #handle config youtube
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm.png',1)
                img = cv2.putText(img, 'Change Your Stream Key?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 5, cv2.LINE_AA)
                img = cv2.putText(img, 'Change Your Stream Key?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)   
                current_screen=2
            elif current_screen==1: #handle confirmed shutdown
                os.system("sudo shutdown -h now")
            elif current_screen==2: #handle config youtube confirmed
                ConfigYouTube()
                current_screen=SCREEN_MENU
            elif current_screen==3: #handle config wifi confirmed
                ConfigWiFi()
                current_screen=SCREEN_MENU
            elif current_screen==4: #handle start streaming confirmed
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
                current_screen=5
                StreamIt()
                current_screen=SCREEN_MENU
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
        elif (x>465 and x<627 and y>294 and y<420):
            if current_screen==SCREEN_MENU: #handle config wifi 
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm.png',1)
                img = cv2.putText(img, 'Config WiFi?', (172, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
                img = cv2.putText(img, 'Config WiFi?', (172, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)
                current_screen=3
            elif current_screen==1 or current_screen==2 or current_screen==3 or current_screen==4: #handle No
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
                current_screen=SCREEN_MENU
        cv2.imshow(WINDOW_NAME,img)

user_tapped_exit=False
current_screen=SCREEN_MENU
img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)


# setup the GUI window and mouse callback routine
cv2.namedWindow(WINDOW_NAME,0)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_AUTOSIZE, cv2.WINDOW_AUTOSIZE);
cv2.imshow(WINDOW_NAME,img)
cv2.setMouseCallback(WINDOW_NAME, MouseHandler)

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (720, 480)
camera.framerate = 30
camera.rotation = 180
rawCapture = PiRGBArray(camera, size=(720, 480) )

# Loop forever until a keyboard key is hit or they close it through the GUI
while not user_tapped_exit:
    k = cv2.waitKey(1)

cv2.destroyAllWindows()
exit()
