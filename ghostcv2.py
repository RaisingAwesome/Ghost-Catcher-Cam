import cv2
import os
from pymouse import PyMouse
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import random
import threading

os.putenv('SDL_VIDEODRIVER','fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
SCREEN_MENU=0
MOUSE_IGNORE=False
WINDOW_NAME="mywindow"
EVENT_STARTED=False
START_STREAM=False
STREAMING=False
START_SCANNING=False
SCANNING=False
PEG_AUDIO=False
START_PEG_AUDIO=False

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
    
    global current_screen, WINDOW_NAME, img, camera, rawCapture, SCREEN_MENU, STREAMING
    global START_SCANNING, SCANNING
    start_time=time.time()
    
    current_screen=5
    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")

    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/camera.png',1)
    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(700)
                
    # allow the camera to warmup
    time.sleep(0.1)
    os.system("sudo chmod +777 /home/pi/Ghost-Catcher-Cam/stop")
    os.system("sudo rm /home/pi/Ghost-Catcher-Cam/stop") #this will let us stop the stream

    os.system("sudo touch /home/pi/Ghost-Catcher-Cam/stop") #by creating an empty file named stop.  Once it has a q in it, ffmpeg will get the q and then stop
    os.system("sudo chmod +777 /home/pi/Ghost-Catcher-Cam/stop")
    
    # Get the current Youtube stream key
    streamkeyfile=open("streamkey.cfg","r")
    streamkey=streamkeyfile.read()
    streamkeyfile.close()
    # just in case there is some sloppy hand typing going on, we'll strip off any white space
    streamkey=streamkey.rstrip()
    
    # Start streaming with ffmpeg
    streamkey="</home/pi/Ghost-Catcher-Cam/stop /usr/bin/ffmpeg -f lavfi -i anullsrc -f x11grab -framerate 30 -video_size 720x480 -i :0.0 -f flv -s 720x480 rtmp://a.rtmp.youtube.com/live2/" + streamkey + " >/dev/null 2>>Capture.log &"
    os.system(streamkey)
    
    HideMouse()
    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/nightvision.wav & ")

    # capture frames from the camera
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    	# grab the raw NumPy array representing the image, then initialize the timestamp
    	# and occupied/unoccupied text
        img = frame.array
        
        cv2.putText(img, 'Normal', (180, 459), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, '100', (635, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(img, '100', (635, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, '70.2F', (170, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(img, '70.2F', (170, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), (210,20),cv2.FONT_HERSHEY_SIMPLEX, .9, (255, 255, 255), 2, cv2.LINE_AA)
        overlay=cv2.imread('/home/pi/Ghost-Catcher-Cam/hud.png')
        img = cv2.addWeighted(img,1.0,overlay,1,0)
        
        #overlay=cv2.imread('/home/pi/Ghost-Catcher-Cam/ghost.png')
        
        if SCANNING:
            overlay=img.copy()
            cv2.rectangle(overlay,(315,406),(416,472),(0,0,0),-1)
            img = cv2.addWeighted(overlay,.6,img,.4,0)
            cv2.putText(img, "scanning", (230, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 6, cv2.LINE_AA)
            UpdateAudioGraphic()
            
            time_left=13-seconds_between(start_time,time.time())
            if time_left>9:
                cv2.putText(img, str(time_left), (270, 310), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 6, cv2.LINE_AA)
            else:
                cv2.putText(img, str(time_left), (330, 310), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 6, cv2.LINE_AA)

        cv2.imshow(WINDOW_NAME, img)
        key = cv2.waitKey(1)

    	# clear the stream in preparation for the next frame
        rawCapture.truncate(0)

    	# if the screen was tapped, break from the loop
        if START_SCANNING:
            START_SCANNING=False
            SCANNING=True
            start_time=time.time()         
            t=threading.Timer(13.0,StopScanning)
            t.start()
            t1=threading.Timer(.5,PlayScanning)
            t1.start()
            
        if current_screen==SCREEN_MENU:
    	    os.system("echo 'q' >stop") #this simulates a keypress of the letter q which stops ffmpeg.  it's genius
    	    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/shutdown.wav &")
    	    # above idea came from https://stackoverflow.com/questions/9722624/how-to-stop-ffmpeg-remotely
    	    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
    	    key = cv2.waitKey(1)
    	    cv2.imshow(WINDOW_NAME, img)
    	    STREAMING=False
    	    break

def UpdateAudioGraphic():
    global PEG_AUDIO, START_PEG_AUDIO
    if START_PEG_AUDIO:
        START_PEG_AUDIO=False
        PEG_AUDIO=True
        t=threading.Timer(1.5,EndPeakAudio)
        t.start()
    if PEG_AUDIO:
        the_peak=20
    else:
        the_peak=random.randrange(20)
    if the_peak>5:
        cv2.rectangle(img,(644,397),(692,413),(0,255,255),-1)
    if the_peak>8:
        cv2.rectangle(img,(644,377),(692,393),(0,255,255),-1)
    if the_peak>10:
        cv2.rectangle(img,(644,357),(692,373),(0,255,255),-1)
    if the_peak>15:
        cv2.rectangle(img,(644,337),(693,353),(0,0,255),-1)
    if the_peak>18:
        cv2.rectangle(img,(644,317),(693,333),(0,0,255),-1)

def EndPeakAudio():
    global PEG_AUDIO
    PEG_AUDIO=False
    
def seconds_between(d1, d2):
    return (abs(int(d1-d2)))

def PlayScanning():
    delay=2 + random.randrange(10)
    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/static.wav &")
    
    t=threading.Timer(delay,PlayScannedAudio)
    t.start()
    
def PlayScannedAudio():
    global START_PEG_AUDIO
    START_PEG_AUDIO=True
    os.system("(aplay -q /home/pi/Ghost-Catcher-Cam/sounds/mom.wav) & ")
    
def StopScanning():
    global SCANNING
    SCANNING=False
    
def ConfigYouTube():
    global img, WINDOW_NAME
    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm2.png',1)
    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(1)
    my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Attach Keyboard and Enter YouTube Stream Key:' --entry --width=300 --height=200 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/temp_streamkey.cfg")
    if not IsCanceled("/home/pi/Ghost-Catcher-Cam/temp_streamkey.cfg"):
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        # do the copying
        os.system("cp /home/pi/Ghost-Catcher-Cam/temp_streamkey.cfg /home/pi/Ghost-Catcher-Cam/streamkey.cfg")
        my_result=os.system("DISPLAY=:0.0 zenity --title='WiFi Config' --info='Stream Set, Good Job.' --width=100 --height=100")
    else:
        os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
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

def TriggerEvent():
    print("eventtriggered")
    
def ConfigWiFi():
    global img, WINDOW_NAME
    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")
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
        os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")
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
        else:
            os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
    else:
        os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
    k=cv2.waitKey(1)

def MouseHandler(event, x, y, flags, param):
    #Handle screen taps based on what screen is showing
    global user_tapped_exit, current_screen, img,WINDOW_NAME, MOUSE_IGNORE, START_STREAM
    global START_SCANNING, SCANNING
    if MOUSE_IGNORE:
        return
    if event==cv2.EVENT_LBUTTONDOWN:
        if not SCANNING:
            os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/bink.wav &")
    elif event==cv2.EVENT_LBUTTONUP:
        # First check if we are streaming.  I fos, send the flag to abort
        if STREAMING:
            if (x>315 and x<412 and y>406 and y<472 and not SCANNING and not START_SCANNING):
                START_SCANNING=True
            elif (not SCANNING  and not START_SCANNING):
                current_screen=SCREEN_MENU
            return
        elif (x>82 and x<252 and y>90 and y<217 and current_screen==SCREEN_MENU): #handle go live tap
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
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/shutdown.wav &")
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/exit.png',1)
                cv2.imshow(WINDOW_NAME,img)
                k=cv2.waitKey(2000)
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
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/shutdown.wav &")
                os.system("( sleep 5 ; sudo shutdown -h now --no-wall ) &")
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/exit.png',1)
                cv2.imshow(WINDOW_NAME,img)
                k=cv2.waitKey(4000)
                os.system("sudo sh -c 'echo \"0\" > /sys/class/backlight/soc\:backlight/brightness'")
                exit()
            elif current_screen==2: #handle config youtube confirmed
                ConfigYouTube()
                current_screen=SCREEN_MENU
            elif current_screen==3: #handle config wifi confirmed
                ConfigWiFi()
                current_screen=SCREEN_MENU
            elif current_screen==4: #handle start streaming confirmed
                START_STREAM=True
        elif (x>465 and x<627 and y>294 and y<420):
            if current_screen==SCREEN_MENU: #handle config wifi 
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm.png',1)
                img = cv2.putText(img, 'Config WiFi?', (172, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
                img = cv2.putText(img, 'Config WiFi?', (172, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)
                current_screen=3
            elif current_screen==1 or current_screen==2 or current_screen==3 or current_screen==4: #handle No
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
                current_screen=SCREEN_MENU
        cv2.imshow(WINDOW_NAME,img)

# Begin Main
user_tapped_exit=False
current_screen=SCREEN_MENU
img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
random.seed()
# Set Display Brightness to maximum
os.system("sudo chmod a+rw /sys/class/backlight/soc\:backlight/brightness")
os.system("sudo sh -c 'echo \"1\" > /sys/class/backlight/soc\:backlight/brightness'")
# setup the GUI window and mouse callback routine
cv2.namedWindow(WINDOW_NAME,0)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_AUTOSIZE, cv2.WINDOW_AUTOSIZE);
cv2.imshow(WINDOW_NAME,img)
cv2.setMouseCallback(WINDOW_NAME, MouseHandler)

os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/331620__hykenfreak__spooky-sucking-air.wav &")
# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (720, 480)
camera.framerate = 30
camera.rotation = 180
rawCapture = PiRGBArray(camera, size=(720, 480) )
trigger_time=100

# Loop forever until a keyboard key is hit or they close it through the GUI
while not user_tapped_exit:
    #if (time.gmtime()>trigger_time):
    #    TriggerEvent()
    #    trigger_time=time.gmtime()+60*10+(random.randrange(15)*60)
        
    k = cv2.waitKey(10)
    if START_STREAM:
        STREAMING=True
        START_STREAM=False
        StreamIt()
        
        
cv2.destroyAllWindows()
exit()