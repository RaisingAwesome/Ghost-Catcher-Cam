import cv2
import os
from pymouse import PyMouse
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import random
import threading

# Setup the Touchscreen
os.putenv('SDL_VIDEODRIVER','fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# Global Variables
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
TOTAL_RADIO_FILES=2
START_FACE_DETECTED=False
FACE_DETECTED=False
START_DETECTION_MODE=False
DETECTION_MODE=False
DETECTION_MODE=False
ACTIVITY_COUNT=0
VOLUME=70
FRAMES_TO_PERSIST=10
MIN_SIZE_FOR_MOVEMENT = 2000
MOVEMENT_DETECTED_PERSISTENCE = 100
motion_delay_counter=1
MOTION_DETECTED=False
first_frame = None
hud="/home/pi/Ghost-Catcher-Cam/hud.png"
ALLOW_BEEP=False


def HideMouse():
    # Click the mouse out of the view.  for some reason, even though I hide it in the operating system, it shows when streaming.
    global MOUSE_IGNORE
    
    MOUSE_IGNORE=True #don't want to register a real click that the logic will catch.  6 will be caught and ignored by the handler
    m = PyMouse()
    m.click(720, 480, 1)
    k=cv2.waitKey(10) # allow time to process without problems
    MOUSE_IGNORE=False

def DetectObject():
    # When Detection Mode is on, this will look for a face and
    # Circle it for one frame
    global object_cascade, img, object_cascade, START_FACE_DETECTED, MOTION_DETECTED
    
    # If we are still counting down, exit the routine until we reach zero
    if DETECTION_COUNTDOWN:
        return
    
    frame_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.equalizeHist(frame_gray)
    
    if not MOTION_DETECTED:
        # We check for motion to prevent seeing something over and over and over again.
        DetectMotion(frame_gray)
    
    if MOTION_DETECTED:
        #-- Detect objects
        faces = object_cascade.detectMultiScale(frame_gray)
        if len(faces)>0:
            if not FACE_DETECTED:
                START_FACE_DETECTED=True
                my_random=random.randrange(8)
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound" + str(my_random) + ".wav &")
                for (x,y,w,h) in faces:
                    center = (x + w//2, y + h//2)
                    img = cv2.ellipse(img, center, (w//2, h//2), 0, 0, 360, (0, 0, 255), 4)
                
def DetectMotion(gray):
    # Modified version of https://github.com/methylDragon/opencv-motion-detector/blob/master/Motion%20Detector.py
    global first_frame, motion_delay_counter, MOTION_DETECTED
     # Set transient motion detected as false
    
    motion_delay_counter += 1
    if motion_delay_counter > FRAMES_TO_PERSIST:
        motion_delay_counter = 0
    else:
        return

    # Blur it to remove camera noise (reducing false positives)
    next_frame = cv2.GaussianBlur(gray, (21, 21), 0)

    # If the first frame is nothing, initialise it
    if first_frame is None: first_frame = next_frame

    # Compare the two frames, find the difference
    frame_delta = cv2.absdiff(first_frame, next_frame)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

    # Fill in holes via dilate(), and find contours of the thesholds
    thresh = cv2.dilate(thresh, None, iterations = 2)
    _, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    first_frame=next_frame
    # loop over the contours
    if len(cnts)==0:
        return
    else:
        for c in cnts:
            # Save the coordinates of all found contours
            (x, y, w, h) = cv2.boundingRect(c)
            
            # If the contour is too small, ignore it, otherwise, there's transient
            # movement
            if cv2.contourArea(c) > MIN_SIZE_FOR_MOVEMENT:
                # set up a timer to stop detecting motion for a 5 seconds and instead
                # it will hunt for objects back in DetectObject
                MOTION_DETECTED=True
                motion_timer=threading.Timer(5,EndMotionDetected)
        return
    
def EndMotionDetected():
    global MOTION_DETECTED
    MOTION_DETECTED=False
    
def EndFaceDetection():
    # When a face is detected, it shows the word Anomaly
    # for 15 seconds.  This turns the display off once
    # time is up.
    global FACE_DETECTED
    FACE_DETECTED=False

def StreamIt():
    # The main routine that streams the camera
    # and determines what to show on the dipslay
    # Reference - http://www.pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/
    
    global current_screen, WINDOW_NAME, img, camera, rawCapture, SCREEN_MENU, STREAMING
    global START_SCANNING, SCANNING, DETECTION_MODE, ACTIVITY_COUNT, START_FACE_DETECTED
    global FACE_DETECTED, ACTIVITY_COUNT, start_time, DETECTION_COUNTDOWN, hud
    global ALLOW_BEEP
    start_time=time.time()
    
    current_screen=5
    hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/hud.png')
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
    streamkeyfile=open("/home/pi/Ghost-Catcher-Cam/streamkey.cfg","r")
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
        
        if DETECTION_MODE:
            DetectObject()
            if START_FACE_DETECTED:
                START_FACE_DETECTED=False
                if not FACE_DETECTED:
                    FACE_DETECTED=True
                    face_thread=threading.Timer(15,EndFaceDetection)
                    face_thread.start()
                    ACTIVITY_COUNT=ACTIVITY_COUNT + 1
            elif FACE_DETECTED:
                cv2.putText(img, 'Anomaly', (180, 454), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)        
            else:
                cv2.putText(img, 'Sensing', (180, 454), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
        else:
            cv2.putText(img, 'Normal', (180, 454), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.putText(img, str(ACTIVITY_COUNT), (635, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(img, str(ACTIVITY_COUNT), (635, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, '70.2F', (170, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(img, '70.2F', (170, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(img, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), (210,20),cv2.FONT_HERSHEY_SIMPLEX, .9, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Overlay the hud
        img = cv2.addWeighted(img,1.0,hud,1.0,0)

        if SCANNING:
            cv2.putText(img, "scanning", (230, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 6, cv2.LINE_AA)
            UpdateAudioGraphic()
            
            time_left=13-seconds_between(start_time,time.time())
            if time_left>9:
                cv2.putText(img, str(time_left), (270, 310), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 6, cv2.LINE_AA)
            else:
                cv2.putText(img, str(time_left), (330, 310), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 6, cv2.LINE_AA)
        elif DETECTION_MODE:
            if DETECTION_COUNTDOWN:
                time_left=10-seconds_between(start_time,time.time())
                
                cv2.putText(img, "Stay Out of View!", (110, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 8, cv2.LINE_AA)
                cv2.putText(img, "Stay Out of View!", (110, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3, cv2.LINE_AA)
                if time_left>9:
                    cv2.putText(img, str(time_left), (270, 310), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 6, cv2.LINE_AA)
                elif time_left>-1:
                    cv2.putText(img, str(time_left), (330, 310), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 255), 6, cv2.LINE_AA)
                else:
                    ALLOW_BEEP=False
                    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/403686__dbkeebler__sfx-shhhh.wav &")
                    DETECTION_COUNTDOWN=False
                
        cv2.imshow(WINDOW_NAME, img)
        key = cv2.waitKey(1)

    	# clear the stream in preparation for the next frame
        rawCapture.truncate(0)

    	# if the screen was tapped, break from the loop
        if START_SCANNING:
            START_SCANNING=False
            DETECTION_MODE=False
            hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/hud_scanning.png')
            SCANNING=True
            start_time=time.time()         
            t=threading.Timer(14.0,StopScanning)
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
    # This simulates audio meter
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
    # PEG_Audio is used to max out the audio meter
    # on demand for a set time.  This is a used by a timer
    # thread to stop the pegging.
    global PEG_AUDIO
    PEG_AUDIO=False
    
def seconds_between(d1, d2):
    # Just a quick way to determine # of seconds between
    # two times.
    return (abs(int(d1-d2)))

def PlayScanning():
    # Play the radio static.  Roll the 13 sided die to
    # determine if a sound will be played.
    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/static.wav &")

    # 1 in 13 chance to hear something spooky
    dice=random.randrange(13)
    
    # dice=12 # eliminate this after you know the rest of the audio strategy works
    if (dice==12):
        delay=2 + random.randrange(10)
        t=threading.Timer(delay,PlayScannedAudio)
        t.start()
    
def PlayScannedAudio():
    # Called randomly to play a random file
    global START_PEG_AUDIO
    START_PEG_AUDIO=True
    num=random.randrange(TOTAL_RADIO_FILES)
    os.system("(aplay -q /home/pi/Ghost-Catcher-Cam/sounds/radio/" + str(num) + ".wav) & ")
    ACTIVITY_COUNT=ACTIVITY_COUNT+1
    
def StopScanning():
    # Used by a timer thread to end the 13 second audio
    # scan routine
    global SCANNING, hud
    SCANNING=False
    hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/hud.png')
    
def ConfigYouTube():
    # Routine to prompt for the Youtube Streamkey
    global img, WINDOW_NAME
    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm2.png',1)
    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(1)
    
    my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Attach Keyboard and Enter YouTube Stream Key:' --entry --width=680 --height=480 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/temp_streamkey.cfg")
    if not IsCanceled("/home/pi/Ghost-Catcher-Cam/temp_streamkey.cfg"):
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        # do the copying
        os.system("cp /home/pi/Ghost-Catcher-Cam/temp_streamkey.cfg /home/pi/Ghost-Catcher-Cam/streamkey.cfg")
        
        my_result=os.system("DISPLAY=:0.0 zenity --title='WiFi Config' --info='Stream Set, Good Job.' --width=680 --height=480")
    else:
        os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
    cv2.imshow(WINDOW_NAME,img)

def UpdateWiFi():
    # Used to prompt for the wifi credentials
    
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
    # Used to check the input from the Zenity Dialogs to see
    # if the user canceled when configuring the Youtube
    # Streamkey or Wifi credentials
    myfile=open(the_file,"r")
    the_value=myfile.read()
    myfile.close()
    if len(the_value)<5:
        return True
    else:
        return False

def ConfigWiFi():
    # Routine to allow typing in custom WiFi Credentials
    
    global img, WINDOW_NAME
    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm2.png',1)
    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(1)
    
    my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Attach Keyboard and Enter SSID:' --entry --width=680 --height=480 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/temp_wifi_ssid.cfg")
    if not IsCanceled("/home/pi/Ghost-Catcher-Cam/temp_wifi_ssid.cfg"):
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        
        my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Enter Password:' --entry --width=680 --height=480 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/temp_wifi_password.cfg")    
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")
        if not IsCanceled("/home/pi/Ghost-Catcher-Cam/temp_wifi_password.cfg"):
            # do the copying
            UpdateWiFi()
            
            my_result=os.system("DISPLAY=:0.0 zenity --title='WiFi Config' --info='WiFi Reset!  Tap to Reboot' --width=680 --height=480")
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
    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(1)

def StartDetectionMode():
    # Starts the countdown for Detection Mode during Streaming
    global START_DETECTION_MODE, DETECTION_MODE, DETECTION_COUNTDOWN,start_time,hud

    START_DETECTION_MODE=False
    DETECTION_COUNTDOWN=True
    DETECTION_MODE=True
    start_time=time.time()
    countdown_thread=threading.Timer(1,BeepEverySecond)
    countdown_thread.start()
    hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/hud_cancel.png')

def BeepEverySecond():
    # Called by the countdown_thread.  
    # A thread that makes a beep every second until someone flags with ALLOW_BEEP
    global ALLOW_BEEP
    ALLOW_BEEP=True
    for i in range(10):
        if not ALLOW_BEEP:
            break
        os.system("(aplay -q /home/pi/Ghost-Catcher-Cam/sounds/202193__thomasevd__10-second-countdown.wav) &")
        time.sleep(1)

    
def MouseHandler(event, x, y, flags, param):
    # Handle Screen Taps based on what screen is showing
    # and what routines where running
    global user_tapped_exit, current_screen, img,WINDOW_NAME, MOUSE_IGNORE, START_STREAM
    global START_SCANNING, SCANNING, DETECTION_MODE, START_DETECTION_MODE, VOLUME,hud
    global ALLOW_BEEP
    if MOUSE_IGNORE:
        return
    if event==cv2.EVENT_LBUTTONDOWN:
        if not SCANNING:
            os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/bink.wav &")
        else:
            os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
        return    
    elif event==cv2.EVENT_LBUTTONUP:
        # First check if we are streaming.  I fos, send the flag to abort
        
        if STREAMING:
            if (x>315 and x<412 and y>406 and y<472 and not SCANNING and not START_SCANNING and not DETECTION_MODE and not START_DETECTION_MODE):
                START_SCANNING=True
            elif (x>426 and x<562 and y>405 and y<468):
                if (not SCANNING and not START_SCANNING and not DETECTION_MODE and not START_DETECTION_MODE):
                    StartDetectionMode()
                elif (DETECTION_MODE or START_DETECTION_MODE):
                    # Kill detection Mode
                    DETECTION_MODE=False
                    START_DETECTION_MODE=False
                    hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/hud.png')
                    ALLOW_BEEP=False
                else:
                    os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
            elif (not SCANNING  and not START_SCANNING and not DETECTION_MODE and not START_DETECTION_MODE):
                current_screen=SCREEN_MENU
            
            HideMouse()    
            return
        elif (x>82 and x<252 and y>90 and y<217 and current_screen==SCREEN_MENU): 
            # Handle the Go live tap
            current_screen=4
            img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm.png',1)
            img = cv2.putText(img, 'Start Streaming!?', (67, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
            img = cv2.putText(img, 'Start Streaming!?', (67, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)
            cv2.imshow(WINDOW_NAME,img)
        elif (x>465 and x<627 and y>90 and y<217):
            if current_screen==SCREEN_MENU: 
                # Handle the tapped power button
                current_screen=1
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm.png',1)
                img = cv2.putText(img, 'Turn Off Camera?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
                img = cv2.putText(img, 'Turn Off Camera?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)  
                cv2.imshow(WINDOW_NAME,img)
            elif current_screen==1:
                # Handle Shutting Down to Desktop
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/shutdown.wav &")
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/exit.png',1)
                cv2.imshow(WINDOW_NAME,img)
                k=cv2.waitKey(2000)
                user_tapped_exit=True
            else:
                # Handle clicking power region without a screen that needs it.
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
                HideMouse()
        elif (x>82 and x<252 and y>294 and y<420):
            if current_screen==SCREEN_MENU: #handle config youtube
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm.png',1)
                img = cv2.putText(img, 'Change Your Stream Key?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 5, cv2.LINE_AA)
                img = cv2.putText(img, 'Change Your Stream Key?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.imshow(WINDOW_NAME,img)
                current_screen=2
                HideMouse()
                return
            elif current_screen==1: 
                # Handle confirmed shutdown
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
                return
            elif current_screen==3: #handle config wifi confirmed
                ConfigWiFi()
                current_screen=SCREEN_MENU
                return
            elif current_screen==4: #handle start streaming confirmed
                START_STREAM=True
                return
            else:
                # Handle hitting the youtube button region on a screen that won't do anything
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
                return
        elif (x>465 and x<627 and y>294 and y<420):
            if current_screen==SCREEN_MENU: #handle config wifi 
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/confirm.png',1)
                img = cv2.putText(img, 'Config WiFi?', (172, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
                img = cv2.putText(img, 'Config WiFi?', (172, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)
                cv2.imshow(WINDOW_NAME,img)
                current_screen=3
                return
            elif current_screen==1 or current_screen==2 or current_screen==3 or current_screen==4: 
                # Handle No
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)
                cv2.imshow(WINDOW_NAME,img)
                current_screen=SCREEN_MENU
                return
            else:
                # Handle if they hit the Wifi/No region on a screen that doesn't do anything with it.
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
                cv2.imshow(WINDOW_NAME,img)
                return
        elif (x>330 and x<400 and y>283 and y<329 and current_screen==SCREEN_MENU):
            # Handle volume Up
            VOLUME=VOLUME+3
            if (VOLUME>100):
                VOLUME=100
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
            else:
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/volumeup.wav &")
            os.system("echo \"" + str(VOLUME) + "\" > /home/pi/Ghost-Catcher-Cam/volume.cfg &")
            os.system("amixer -q set PCM " + str(VOLUME) + "%")                
            return
        elif (x>330 and x<400 and y>395 and y<453 and current_screen==SCREEN_MENU):
            VOLUME=VOLUME-3
            if (VOLUME<70):
                VOLUME=70
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
            else:
                os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/volumedown.wav &")
            os.system("echo \"" + str(VOLUME) + "\" > /home/pi/Ghost-Catcher-Cam/volume.cfg &")
            os.system("amixer -q set PCM " + str(VOLUME) + "%")
            return
        else:
            # Handle a tap in a region on a screen that had no response
            os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
            HideMouse()
        return

def GetVolume():
    # Retrieves last set volume
    global VOLUME
    fd=open("/home/pi/Ghost-Catcher-Cam/volume.cfg","r")
    VOLUME=int(fd.read())
    fd.close()
    
# Main
user_tapped_exit=False
current_screen=SCREEN_MENU
img = cv2.imread('/home/pi/Ghost-Catcher-Cam/gui.png',1)

# Seed a random object with the current time
random.seed()

# Set Display Brightness to maximum
os.system("sudo chmod a+rw /sys/class/backlight/soc\:backlight/brightness")
os.system("sudo sh -c 'echo \"1\" > /sys/class/backlight/soc\:backlight/brightness'")

# Setup the OpenCV driven GUI window and mouse callback routine
cv2.namedWindow(WINDOW_NAME,0)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_AUTOSIZE, cv2.WINDOW_AUTOSIZE);
cv2.imshow(WINDOW_NAME,img)
cv2.setMouseCallback(WINDOW_NAME, MouseHandler)

# Play the startup sound
GetVolume()
os.system("amixer -q set PCM " + str(VOLUME) + "%")
os.system("aplay -q /home/pi/Ghost-Catcher-Cam/sounds/331620__hykenfreak__spooky-sucking-air.wav &")

# Initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (720, 480)
camera.framerate = 30
camera.rotation = 180
rawCapture = PiRGBArray(camera, size=(720, 480) )
trigger_time=100

# OpenCV Object Classification Setup
object_cascade = cv2.CascadeClassifier()

# Load the object cascade for face detection
# XML file retrieved from https://github.com/opencv/opencv/tree/master/data/haarcascades/haarcascade_frontalface_alt.xml
# fully body:  /home/pi/Ghost-Catcher-Cam/opencv/haarcascade_fullbody.xml
# face: /home/pi/Ghost-Catcher-Cam/opencv/haarcascade_frontalface_alt.xml
if not object_cascade.load('/home/pi/Ghost-Catcher-Cam/opencv/haarcascade_frontalface_alt.xml'):
    print('--(!)Error loading object cascade')
    exit(0)

# Loop forever until a keyboard key is hit or they close it through the GUI
while not user_tapped_exit:
    k = cv2.waitKey(10)
    if START_STREAM:
        # Handles the transition from the GUI to the
        # Stream Display
        STREAMING=True
        START_STREAM=False
        StreamIt()
        
# Cleanup and exit
cv2.destroyAllWindows()
exit()