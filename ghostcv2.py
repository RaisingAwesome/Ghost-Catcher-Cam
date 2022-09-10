import cv2
import os
from pymouse import PyMouse
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import random
import threading
import datetime
import socket
import psutil
import math
# Setup the Touchscreen
os.putenv('SDL_VIDEODRIVER','fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# Global Variables
SCREEN_MENU=0
MOUSE_IGNORE=False
WINDOW_NAME="That Paranormal"
EVENT_STARTED=False
START_STREAM=False
STREAMING=False
START_SCANNING=False
SCANNING=False
PEG_AUDIO=False
START_PEG_AUDIO=False
START_FACE_DETECTED=False
FACE_DETECTED=False
START_DETECTION_MODE=False
DETECTION_MODE=False
DETECTION_COUNTDOWN=False
ACTIVITY_COUNT=0
MATCH=100 #used to show certainty of audio detected
VOLUME=100
FRAMES_TO_PERSIST=10
MIN_SIZE_FOR_MOVEMENT = 2000
MOVEMENT_DETECTED_PERSISTENCE = 100
motion_delay_counter=1
MOTION_DETECTED=False
first_frame = None
hud="/home/pi/Ghost-Catcher-Cam/images/hud.png"
ALLOW_BEEP=False
WIFI_CONNECTED=False
USB_CONNECTED=True
RECORDING=True
myangle=-85
geiger_duration=0
DETECTED_WORDS=""

TOTAL_RADIO_FILES=0 # This will be dynamically set when it reads words.txt
SOUND_TRACK=0
the_sounds=""

last_detect_time=time.time()
next_geiger_time=time.time()+60
last_geiger_time=time.time()
last_time_touched=time.time()

def HideMouse():
    # Click the mouse out of the view.  for some reason, even though I hide it in the operating system, it shows when streaming.
    global MOUSE_IGNORE

    MOUSE_IGNORE=True #don't want to register a real click that the logic will catch.  6 will be caught and ignored by the handler
    m = PyMouse()
    m.click(720, 480, 1)
    k=cv2.waitKey(10) # allow time to process without problems
    MOUSE_IGNORE=False

def GetTemp():
    os.system("vcgencmd measure_temp >/home/pi/Ghost-Catcher-Cam/ramdisk/the_temp")
    fileObject = open("/home/pi/Ghost-Catcher-Cam/ramdisk/the_temp", "r")
    the_temp = fileObject.read()
    the_temp=the_temp[5:7]
    return the_temp

def DetectObject():
    # When Detection Mode is on, this will look for a face and
    # Circle it for one frame
    global object_cascade, img, object_cascade, START_FACE_DETECTED, MOTION_DETECTED, last_detect_time, DETECTION_COUNTDOWN

    # If we are still counting down, exit the routine until we reach zero
    if DETECTION_COUNTDOWN:
        return

    if time.time()-last_detect_time<.5:
        return

    last_detect_time=time.time()

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
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound" + str(my_random) + ".wav &")
                for (x,y,w,h) in faces:
                    DrawBody(x,y,w,h,img)

def DrawBody(x,y,w,h,img):
    center = (x + w//2, y + h//2)
    #head
    img = cv2.ellipse(img, center, (w//3, h//2), 0, 0, 360, (0, 175, 175), 4)
    #body
    img = cv2.line(img, (x+w//2,y+h), (x+w//2,y+h*2), (0, 155, 155), 1)
    DrawLeftArm(x,y,w,h,img,(random.randrange(100)-60));
    DrawRightArm(x,y,w,h,img,(random.randrange(110)-60));

def DrawLeftArm(x,y,w,h,img,angle):
    #Left Arm
    l=2*w//3 #arms length
    x=x+w//2 #point of reference of triangle and technically the arm pit
    y=int(y+(1.25*h)) #y point of reference of traingle and technically the arm pit
    a=int(l*( math.cos( math.radians(angle) )  ) ) #triangle opposite side line segment length
    o=int(l*( math.sin( math.radians(angle) )  ) ) #triangle opposite side line segment length
    xe=x-a #end of arm x coordinate
    ye=y-o #end of arm y coordinate

    img = cv2.line(img, (xe,ye), (x,y), (0, 155, 155), 5)

def DrawRightArm(x,y,w,h,img,angle):
    #Right Arm
    l=2*w//3 #arms length
    x=x+w//2 #point of reference of triangle and technically the arm pit
    y=int(y+(1.25*h)) #y point of reference of traingle and technically the arm pit
    a=int(l*( math.cos( math.radians(angle) )  ) ) #triangle opposite side line segment length
    o=int(l*( math.sin( math.radians(angle) )  ) ) #triangle opposite side line segment length
    xe=x+a #end of arm x coordinate
    ye=y-o #end of arm y coordinate

    img = cv2.line(img, (xe,ye), (x,y), (0, 155, 155), 5)

def DetectFaceAgain():
    global object_cascade, img

    frame_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.equalizeHist(frame_gray)

    faces = object_cascade.detectMultiScale(frame_gray)
    if len(faces)>0:
        for (x,y,w,h) in faces:
            DrawBody(x,y,w,h,img)

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
    #_, cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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
                motion_timer.start()
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
    global ALLOW_BEEP, RECORDING, myangle, DETECTED_WORDS, MATCH
    start_time=time.time()

    current_screen=5
    hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/images/hud.png')
    os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")

    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/camera.png',1)

    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(700)

    # allow the camera to warmup
    time.sleep(0.1)

    os.system("sudo rm Capture.log 2>/dev/null") #this would grow forever if we don't delete it at the start of each session

    os.system("sudo chmod +777 /home/pi/Ghost-Catcher-Cam/ramdisk/stop 2>/dev/null")
    os.system("sudo rm /home/pi/Ghost-Catcher-Cam/ramdisk/stop 2>/dev/null") #this will let us stop the stream

    os.system("sudo touch /home/pi/Ghost-Catcher-Cam/ramdisk/stop 2>/dev/null") #by creating an empty file named stop.  Once it has a q in it, ffmpeg will get the q and then stop
    os.system("sudo chmod +777 /home/pi/Ghost-Catcher-Cam/ramdisk/stop 2>/dev/null")

    # Get the current Youtube stream key
    streamkeyfile=open("/home/pi/Ghost-Catcher-Cam/config/streamkey.cfg","r")
    streamkey=streamkeyfile.read()
    streamkeyfile.close()
    # just in case there is some sloppy hand typing going on, we'll strip off any white space
    streamkey=streamkey.rstrip()

    # Start streaming to YouTube with ffmpeg
    the_filename=""
    if (not RECORDING):
         streamkey="</home/pi/Ghost-Catcher-Cam/ramdisk/stop /usr/bin/ffmpeg -v quiet -f pulse -i alsa_output.platform-bcm2835_audio.analog-stereo.monitor -f x11grab -framerate 30 -video_size 720x480 -i :0.0 -f flv -s 854x480 -b:v 1024K -framerate 30 rtmp://a.rtmp.youtube.com/live2/" + streamkey + " &"
    else:
         now = datetime.datetime.now()
         the_filename = "video-" + str(now.hour) + "-" + str(now.minute) + "-" + str(now.second) + ".avi"
#         streamkey="</home/pi/Ghost-Catcher-Cam/ramdisk/stop /usr/bin/ffmpeg -v quiet -f pulse -i alsa_output.platform-bcm2835_audio.analog-stereo.monitor -f x11grab -framerate 30 -video_size 720x480 -i :0.0 -b:v 1M /home/pi/usbdrv/" + the_filename + "  > /home/pi/ffmpg.log 2>&1"
         streamkey="</home/pi/Ghost-Catcher-Cam/ramdisk/stop /usr/bin/ffmpeg -v quiet -f lavfi -i anullsrc -f x11grab -framerate 30 -video_size 720x480 -i :0.0 -f flv -b:v 1M /home/pi/usbdrv/" + the_filename + " &"
    os.system(streamkey)

    HideMouse()
    os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/nightvision.wav & ")

    # capture frames from the camera
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        theTemp=GetTemp()
        # grab the raw NumPy array representing the image, then initialize the timestamp
    	# and occupied/unoccupied text
        img = frame.array
        if not FACE_DETECTED: # did this to speed up processing during face detection
            if not SCANNING and not DETECTION_MODE:
                cv2.rectangle(img,(320,410),(412,470),(0,0,0),-1)
                cv2.rectangle(img,(430,410),(563,470),(0,0,0),-1)

                cv2.rectangle(img,(39,402),(83,417),(0,0,0),-1)
                cv2.rectangle(img,(150,398),(190,417),(0,0,0),-1)
                cv2.ellipse(img, ( 115, 398 ), ( 53, 40 ), 0, 180, 360, ( 0, 0, 0 ), 40, -1 )

            img = cv2.addWeighted(img,1.0,hud,1.0,0)
            cv2.rectangle(img,(644,417),(692,433),(0,255,0),-1)
            cv2.rectangle(img,(644,437),(692,453),(0,255,0),-1)

        if DETECTION_MODE:
            if not FACE_DETECTED:
                # If we saw a face in the last 15 seconds, don't speed up the frame rate
                # by bypassing DetectObject()
                DetectObject()

            if START_FACE_DETECTED:
                START_FACE_DETECTED=False
                if not FACE_DETECTED:
                    FACE_DETECTED=True
                    face_thread=threading.Timer(15,EndFaceDetection)
                    face_thread.start()
                    ACTIVITY_COUNT=ACTIVITY_COUNT + 1
            elif FACE_DETECTED:
                DetectFaceAgain() # this approach keeps the camera fast until something is detected

            if geiger_duration==0: # Prevents overwriting the word Presence
                cv2.putText(img, 'Sensing', (180, 454), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
        elif geiger_duration==0:
            cv2.putText(img, 'Normal', (180, 454), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        tempangle=-85 # intialize the temp angle variable

        if (not DETECTION_COUNTDOWN and not FACE_DETECTED):
            if (geiger_duration>0): # this correlates with the geiger sound still playing
                tempangle=45+random.randrange(40)
                cv2.putText(img, 'Presence', (177, 454), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4, cv2.LINE_AA)

            if myangle>tempangle:
                myangle=myangle-(10/(1+random.randrange(5)))
            else:
                myangle=myangle+(10/(1+random.randrange(5)))

            tempx=int(114 + 60*(math.sin(math.radians(myangle))))
            tempy=int(420 - 60*(math.cos(math.radians(myangle))))
            the_red=0
            the_blue=0
            if (myangle+50>0 and myangle<=55):
                the_blue=255*((myangle+50)/105)
                the_red=255*((myangle+50)/105)
            if (myangle>55):
                the_red=255
                the_blue=255*((90-myangle)/90 )
            img = cv2.line(img, (tempx,tempy), (114,423), (0, the_blue, the_red), 8, cv2.LINE_AA)

            playGeiger()

        if not FACE_DETECTED: # did this to reduce processing time
            cv2.putText(img, str(ACTIVITY_COUNT), (635, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(img, str(ACTIVITY_COUNT), (635, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(img, theTemp, (170, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(img, theTemp, (170, 53), cv2.FONT_HERSHEY_SIMPLEX, .9, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(img, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), (210,20),cv2.FONT_HERSHEY_SIMPLEX, .9, (255, 255, 255), 2, cv2.LINE_AA)

        if SCANNING:
            cv2.putText(img, "Frequency Scanning", (40, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 6, cv2.LINE_AA)
            UpdateAudioGraphic()
            if (DETECTED_WORDS!=""):
                wx=random.randrange(5) #used to make it wiggle like creept text credits
                wy=random.randrange(5)
                wg=0 #used to make it turn white 20% of the time to make it creepy text
                wb=0
                if wx==4:
                    wg=255
                    wb=255
                cv2.putText(img, "Translation",(315, 395), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.putText(img, "Confidence: " + str(MATCH) + "%",(315, 427), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                cv2.putText(img, DETECTED_WORDS, (315+wx, 454+wy), cv2.FONT_HERSHEY_COMPLEX, 1, (wb, wg, 255), 2, cv2.LINE_AA)

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
                    os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/shhhh.wav &")
                    DETECTION_COUNTDOWN=False
                    hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/images/hud_scanning.png')
        cv2.imshow(WINDOW_NAME, img)
        key = cv2.waitKey(1)

    	# clear the stream in preparation for the next frame
        rawCapture.truncate(0)

    	# if the screen was tapped, break from the loop
        if START_SCANNING:
            START_SCANNING=False
            DETECTION_MODE=False
            hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/images/hud_scanning.png')
            SCANNING=True
            start_time=time.time()
            t=threading.Timer(14.0,StopScanning)
            t.start()
            t1=threading.Timer(.5,PlayScanning)
            t1.start()

        if current_screen==SCREEN_MENU:
            os.system("echo 'q' >ramdisk/stop") #this simulates a keypress of the letter q which stops ffmpeg.  it's genius
            os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/shutdown.wav &")
            # above idea came from https://stackoverflow.com/questions/9722624/how-to-stop-ffmpeg-remotely
            showGUI()
            STREAMING=False
            break

def checkIfProcessRunning(processName):
    #Check if there is any running process that contains the given name processName.
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False;

def playGeiger():
    global next_geiger_time, geiger_duration, last_geiger_time
    if (time.time()>next_geiger_time):
       geiger_duration=random.randrange(10)+1
       os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q -d " + str(geiger_duration) + " /home/pi/Ghost-Catcher-Cam/sounds/geiger" + str(random.randrange(2)) + ".wav &")
       next_geiger_time=time.time()+30+random.randrange(60)
       last_geiger_time=time.time()
    if (time.time()-geiger_duration>last_geiger_time):
        geiger_duration=0

def shuffle():
    #used to randomize the order of the values in the array.  Awesomeness.
    global TOTAL_RADIO_FILES, the_sounds
    n = TOTAL_RADIO_FILES        #The number of items left to shuffle (loop invariant) starting with total items.

    while (n > 1):
        k = random.randrange(n)  # 0 <= k < n.
        n=n-1                     # n is now the last pertinent index
        temp = the_sounds[n]     # swap array[n] with array[k] (does nothing if k == n, inherently).
        the_sounds[n] = the_sounds[k]
        the_sounds[k] = temp;

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
    # Play the radio static.  Roll the die to
    # determine if a sound will be played or just play it if they scanned when the geiger was >65.

    global myangle, DETECTED_WORDS

    dice=0
    if myangle>25 and myangle<55:
        dice=random.randrange(2)
    elif myangle>=55:
        dice=1
    else:
        dice=random.randrange(8)
    #dice=1
    if (dice==1):
        delay=2 + random.randrange(8)
        os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/static.wav &")

        t=threading.Timer(delay,PlayScannedAudio)
        t.start()
    else:
        os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/static.wav &")
        DETECTED_WORDS=""

def PlayScannedAudio():
    # Called randomly to play a random file
    global START_PEG_AUDIO, ACTIVITY_COUNT, SOUND_TRACK, TOTAL_RADIO_FILES,the_sounds, myangle,DETECTED_WORDS, MATCH
    START_PEG_AUDIO=True #Starts the EQ bar animation on the right of the screen
    MATCH=abs(int(myangle)) # Use this to give the probability match based on when they hit it.
    myangle=88 #peg the EMF meter
    # Following line was for use with wav files but the user wanted just words.
    #os.system("(aplay -q /home/pi/Ghost-Catcher-Cam/sounds/radio/" + str(the_sounds[SOUND_TRACK]) + ".wav) & ")
    DETECTED_WORDS=(the_sounds[SOUND_TRACK]).replace("\n","")
    Speak()
    ACTIVITY_COUNT=ACTIVITY_COUNT+1

def StopScanning():
    # Used by a timer thread to end the 13 second audio
    # scan routine
    global SCANNING, hud, DETECTED_WORDS
    SCANNING=False
    DETECTED_WORDS=""
    hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/images/hud.png')

def ConfigYouTube():
    # Routine to prompt for the Youtube Streamkey
    global img, WINDOW_NAME
    os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/confirm2.png',1)
    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(1)

    my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Attach Keyboard and Enter YouTube Stream Key:' --entry --width=680 --height=480 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/config/temp_streamkey.cfg")
    if not IsCanceled("/home/pi/Ghost-Catcher-Cam/config/temp_streamkey.cfg"):
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        # do the copying
        os.system("cp /home/pi/Ghost-Catcher-Cam/config/temp_streamkey.cfg /home/pi/Ghost-Catcher-Cam/config/streamkey.cfg")

        my_result=os.system("DISPLAY=:0.0 zenity --title='WiFi Config' --info='Stream Set, Good Job.' --width=680 --height=480")
    else:
        os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
    showGUI()
def UpdateWiFi():
    # Used to prompt for the wifi credentials

    the_file=open("/home/pi/Ghost-Catcher-Cam/config/temp_wifi_ssid.cfg","r")
    ssid=the_file.read()
    ssid=ssid.rstrip()
    the_file.close
    the_file=open("/home/pi/Ghost-Catcher-Cam/config/temp_wifi_password.cfg","r")
    pwd=the_file.read()
    pwd=pwd.rstrip()
    the_file.close()

    os.system("echo \"ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\\nupdate_config=1\\ncountry=US\\n\\nnetwork={\\nssid=\\\"" + ssid + "\\\"\\npsk=\\\"" + pwd + "\\\"\\nkey_mgmt=WPA-PSK\\n}\" > /home/pi/Ghost-Catcher-Cam/config/tempwifi.cfg")
    os.system("sudo cp /home/pi/Ghost-Catcher-Cam/config/tempwifi.cfg /etc/wpa_supplicant/wpa_supplicant.conf")

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
    os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/confirm2.png',1)
    cv2.imshow(WINDOW_NAME,img)
    k=cv2.waitKey(1)
    my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Attach Keyboard and Enter SSID:' --entry --width=680 --height=480 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/config/temp_wifi_ssid.cfg")
    if not IsCanceled("/home/pi/Ghost-Catcher-Cam/config/temp_wifi_ssid.cfg"):
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        my_result=os.system("echo $(DISPLAY=:0.0 zenity --title='WiFi Config' --text='Enter Password:' --entry --width=680 --height=480 --ok-label='SET') >/home/pi/Ghost-Catcher-Cam/config/temp_wifi_password.cfg")    
        cv2.imshow(WINDOW_NAME,img)
        k=cv2.waitKey(10)
        os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/spooky_sound7.wav & ")
        if not IsCanceled("/home/pi/Ghost-Catcher-Cam/config/temp_wifi_password.cfg"):
            # do the copying
            UpdateWiFi()
            my_result=os.system("DISPLAY=:0.0 zenity --title='WiFi Config' --info='WiFi Reset!  Tap to Reboot' --width=680 --height=480")
            img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/rebooting.png',1)
            cv2.imshow(WINDOW_NAME,img)
            k=cv2.waitKey(2000)
            cv2.destroyAllWindows()
            os.system("( sleep 1 ; sudo reboot )")
            exit()
        else:
            os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
    else:
        os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
    showGUI()
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
    hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/images/hud_cancel.png')

def BeepEverySecond():
    # Called by the countdown_thread.  
    # A thread that makes a beep every second until someone flags with ALLOW_BEEP
    global ALLOW_BEEP
    ALLOW_BEEP=True
    for i in range(10):
        if not ALLOW_BEEP:
            break
        os.system("(XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/202193__thomasevd__10-second-countdown.wav) &")
        time.sleep(1)

def showGUI():
    checkForWiFi()
    img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/gui.png',1)
    if not WIFI_CONNECTED:
        cv2.putText(img, "No WiFi!", (110, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 7, cv2.LINE_AA)
        cv2.putText(img, "No WiFi!", (110, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0, 255), 2, cv2.LINE_AA)
    if not USB_CONNECTED:
        cv2.putText(img, "No USB!", (290, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 7, cv2.LINE_AA)
        cv2.putText(img, "No USB!", (290, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.imshow(WINDOW_NAME,img)

def MouseHandler(event, x, y, flags, param):
    # Handle Screen Taps based on what screen is showing
    # and what routines where running
    global user_tapped_exit, current_screen, img,WINDOW_NAME, MOUSE_IGNORE, START_STREAM
    global START_SCANNING, SCANNING, DETECTION_MODE, START_DETECTION_MODE, VOLUME,hud
    global ALLOW_BEEP, RECORDING, last_time_touched

    if MOUSE_IGNORE:
        return
    if event==cv2.EVENT_LBUTTONDOWN:
        delta_time=time.time()-last_time_touched
        if (delta_time<.5):
            return # prevent the inadvertent bounce tap

        if not SCANNING:
            os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/bink.wav &")
        else:
            os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
        return
    elif event==cv2.EVENT_LBUTTONUP:
        delta_time=time.time()-last_time_touched
        if (delta_time<.5):
            return # prevent the inadvertent bounce tap

        if (delta_time>300):
            #The screen blanks after 5 minutes.  This will suppress the tap to wake it back up if not tapped in 5 minutes
            last_time_touched=time.time()
            return
        else:
            last_time_touched=time.time()

        # First check if we are streaming.  If it is, send the flag to abort
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
                    hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/images/hud.png')
                    ALLOW_BEEP=False
                else:
                    os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
            elif (not SCANNING  and not START_SCANNING and not DETECTION_MODE and not START_DETECTION_MODE):
                current_screen=SCREEN_MENU
            else:
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")

            if DETECTION_MODE:
                hud=cv2.imread('/home/pi/Ghost-Catcher-Cam/images/hud_cancel.png')
                cv2.imshow(WINDOW_NAME,img)
            HideMouse()
            return
        elif (x>82 and x<252 and y>90 and y<217 and current_screen==SCREEN_MENU and WIFI_CONNECTED):
            # Handle the Go live tap
            current_screen=4
            RECORDING=False
            img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/confirm.png',1)
            img = cv2.putText(img, 'Start Streaming!?', (67, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
            img = cv2.putText(img, 'Start Streaming!?', (67, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)
            cv2.imshow(WINDOW_NAME,img)
        elif (x>260 and x<460 and y>90 and y<217 and current_screen==SCREEN_MENU and USB_CONNECTED): 
            # Handle the Record tap
            current_screen=4
            RECORDING=True
            img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/confirm.png',1)
            img = cv2.putText(img, 'Start Recording!?', (67, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
            img = cv2.putText(img, 'Start Recording!?', (67, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)
            cv2.imshow(WINDOW_NAME,img)
        elif (x>465 and x<627 and y>90 and y<217):
            if current_screen==SCREEN_MENU:
                # Handle the tapped power button
                current_screen=1
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/confirm.png',1)
                img = cv2.putText(img, 'Turn Off Camera?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
                img = cv2.putText(img, 'Turn Off Camera?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)  
                cv2.imshow(WINDOW_NAME,img)
            elif current_screen==1:
                # Handle Shutting Down to Desktop
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/shutdown.wav &")
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/exit.png',1)
                cv2.imshow(WINDOW_NAME,img)
                k=cv2.waitKey(2000)
                user_tapped_exit=True
            else:
                # Handle clicking power region without a screen that needs it.
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
                HideMouse()
        elif (x>82 and x<252 and y>294 and y<420):
            if current_screen==SCREEN_MENU: #handle config youtube
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/confirm.png',1)
                img = cv2.putText(img, 'Change Your Stream Key?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 5, cv2.LINE_AA)
                img = cv2.putText(img, 'Change Your Stream Key?', (45, 195), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.imshow(WINDOW_NAME,img)
                current_screen=2
                HideMouse()
                return
            elif current_screen==1:
                # Handle confirmed shutdown
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/shutdown.wav &")
                os.system("( sleep 5 ; sudo shutdown -h now --no-wall ) &")
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/exit.png',1)
                cv2.imshow(WINDOW_NAME,img)
                k=cv2.waitKey(4000)
                if not os.path.exists('/sys/class/backlight'):
                    print ("Not an Adafruit Screen")
                else:
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
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
                return
        elif (x>465 and x<627 and y>294 and y<420):
            if current_screen==SCREEN_MENU: #handle config wifi 
                img = cv2.imread('/home/pi/Ghost-Catcher-Cam/images/confirm.png',1)
                img = cv2.putText(img, 'Config WiFi?', (172, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (0, 0, 0), 7, cv2.LINE_AA)
                img = cv2.putText(img, 'Config WiFi?', (172, 195), cv2.FONT_HERSHEY_SIMPLEX, 2.25, (255, 255, 255), 4, cv2.LINE_AA)
                cv2.imshow(WINDOW_NAME,img)
                current_screen=3
                return
            elif current_screen==1 or current_screen==2 or current_screen==3 or current_screen==4: 
                # Handle No
                showGUI()
                current_screen=SCREEN_MENU
                return
            else:
                # Handle if they hit the Wifi/No region on a screen that doesn't do anything with it.
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
                cv2.imshow(WINDOW_NAME,img)
                return
        elif (x>330 and x<400 and y>273 and y<359 and current_screen==SCREEN_MENU):
            # Handle volume Up
            VOLUME=VOLUME+5
            if (VOLUME>130):
                VOLUME=130
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
            else:
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/volumeup.wav &")
            os.system("echo \"" + str(VOLUME) + "\" > /home/pi/Ghost-Catcher-Cam/config/volume.cfg &")
            os.system("XDG_RUNTIME_DIR=/run/user/1000 pactl set-sink-volume 1 " + str(VOLUME) + "%")                
            return
        elif (x>330 and x<400 and y>395 and y<453 and current_screen==SCREEN_MENU):
            VOLUME=VOLUME-5
            if (VOLUME<50):
                VOLUME=50
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
            else:
                os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/volumedown.wav &")
            os.system("echo \"" + str(VOLUME) + "\" > /home/pi/Ghost-Catcher-Cam/config/volume.cfg &")
            os.system("XDG_RUNTIME_DIR=/run/user/1000 pactl set-sink-volume 1 " + str(VOLUME) + "%")
            return
        else:
            # Handle a tap in a region on a screen that had no response
            os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/419023__jacco18__acess-denied-buzz.wav &")
            HideMouse()
        return

def GetVolume():
    # Retrieves last set volume
    global VOLUME
    fd=open("/home/pi/Ghost-Catcher-Cam/config/volume.cfg","r")
    VOLUME=int(fd.read())
    fd.close()

def checkForWiFi():
    global WIFI_CONNECTED
    try:
        temp=socket.gethostbyaddr("8.8.8.8")
        WIFI_CONNECTED=True
    except:
        WIFI_CONNECTED=False

def Speak():
    global the_sounds, SOUND_TRACK, TOTAL_RADIO_FILES
    pitch=random.randrange(70)
    speed=random.randrange(60)
    dice=random.randrange(4) # echo probability of 1 in 4
    echo=" 3 100 5 50 200 10" #makes an echo

    # 1 in 5 chance of picking a female voice which has 4 types.  Males have 7 types.  Also 1 in 5 to whisper
    gender="+m"
    voice=random.randrange(7)+1
    dice=random.randrange(4)
    if dice==1:
        echo=""
    if dice==1:
        gender="+f"
        voice=random.randrange(4)+1
    elif dice==5:
        gender="+whisper"
        voice=""
    dice=random.randrange(7)
    if dice==0:
        accent="en-us"
    elif dice>0 and dice<3:
        accent="en-us"
    elif dice>2 and dice<5:
        accent="ro"
    elif dice==5:
        accent="en-sc"
    elif dice==6:
        accent="tr"
    os.system("XDG_RUNTIME_DIR=/run/user/1000 espeak -a 200 -v " + accent + gender + str(voice) +" -s " + str(speed + 50) + " -p " + str(30+pitch) + " \"" + the_sounds[SOUND_TRACK] + "\" --stdout | XDG_RUNTIME_DIR=/run/user/1000 play -V0 - pad 0 2 reverb " + echo +" 2>/dev/null")

    SOUND_TRACK=SOUND_TRACK+1
    if SOUND_TRACK>=TOTAL_RADIO_FILES:
        SOUND_TRACK=0
    #keeps from starting over the word list each time the camera is used.
    f = open("/home/pi/Ghost-Catcher-Cam/sounds/radio/current.txt", "w")
    f.write(str(SOUND_TRACK))
    f.close()

def ReadWords():
    global the_sounds,SOUND_TRACK,TOTAL_RADIO_FILES
    f = open('/home/pi/Ghost-Catcher-Cam/sounds/radio/words.txt', 'r+')
    the_sounds = [line for line in f.readlines()]
    f.close()
    TOTAL_RADIO_FILES=len(the_sounds)
    f = open("/home/pi/Ghost-Catcher-Cam/sounds/radio/current.txt", "r")
    SOUND_TRACK=int(f.read())
    f.close()

# Main
user_tapped_exit=False
current_screen=SCREEN_MENU

# Seed a random object with the current time
random.seed()
#shuffle() #randomizes the sequence of songs so it doesn't play the same one twice until all are played once
ReadWords()
# Set Display Brightness to maximum
if not os.path.exists('/sys/class/backlight'):
    print ("Not an Adafruit Screen")
else:
    os.system("sudo chmod a+rw /sys/class/backlight/soc\:backlight/brightness")
    os.system("sudo sh -c 'echo \"1\" > /sys/class/backlight/soc\:backlight/brightness'")

# Setup the OpenCV driven GUI window and mouse callback routine
cv2.namedWindow(WINDOW_NAME,0)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_AUTOSIZE, cv2.WINDOW_AUTOSIZE);
showGUI()
cv2.setMouseCallback(WINDOW_NAME, MouseHandler)

# Play the startup sound
GetVolume()
os.system("XDG_RUNTIME_DIR=/run/user/1000 pactl set-sink-volume 1 " + str(VOLUME) + "%")
os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/331620__hykenfreak__spooky-sucking-air.wav &")

# Initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (720, 480)
camera.framerate = 30
camera.rotation = 0
camera.exposure_mode='auto'
camera.image_effect='denoise'
camera.brightness = 50
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
os.system("XDG_RUNTIME_DIR=/run/user/1000 aplay -q /home/pi/Ghost-Catcher-Cam/sounds/geiger1.wav &")
exit()
