import cv2
import os
from pymouse import PyMouse

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time

os.putenv('SDL_VIDEODRIVER','fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

def StreamIt():
    #from http://www.pyimagesearch.com/2015/03/30/accessing-the-raspberry-pi-camera-with-opencv-and-python/
    # initialize the camera and grab a reference to the raw camera capture
    global screen, tag, img, camera, rawCapture
     
    # allow the camera to warmup
    time.sleep(0.1)
    os.system("sudo chmod +777 /home/tp/RaspberryPiRepositories/Ghost-Catcher-Cam/stop")
    os.system("sudo rm /home/tp/RaspberryPiRepositories/Ghost-Catcher-Cam/stop") #this will let us stop the stream
    
    os.system("sudo touch /home/tp/RaspberryPiRepositories/Ghost-Catcher-Cam/stop") #by creating an empty file named stop.  Once it has a q in it, ffmpeg will get the q and then stop
    os.system("sudo chmod +777 /home/tp/RaspberryPiRepositories/Ghost-Catcher-Cam/stop")
    os.system("sudo </home/tp/RaspberryPiRepositories/Ghost-Catcher-Cam/stop /usr/bin/ffmpeg -f lavfi -i anullsrc -f x11grab -framerate 30 -video_size 480x320 -i :0.0 -f flv -s 480x320 rtmp://a.rtmp.youtube.com/live2/628y-jagt-7b5c-4c9b >/dev/null 2>>Capture.log &")
    
    screen=6 #don't want to register a real click that the logic will catch
    #click the mouse out of the view.  for some reason, even though I hide it in the operating system, it shows when streaming.

    m = PyMouse()
    m.click(479, 319, 1)

    key=cv2.waitKey(100)
    screen=5
    # capture frames from the camera
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    	# grab the raw NumPy array representing the image, then initialize the timestamp
    	# and occupied/unoccupied text
    	img = frame.array
    	img=cv2.resize(img, (480,320),interpolation = cv2.INTER_AREA)
    	
    	img = cv2.putText(img, 'Raising Awesome!', (45, 130), cv2.FONT_HERSHEY_SIMPLEX,
               1.5, (0, 0, 0), 7, cv2.LINE_AA)
        # show the frame
    	cv2.imshow(tag, img)
    	key = cv2.waitKey(1)
     
    	# clear the stream in preparation for the next frame
    	rawCapture.truncate(0)
     
    	# if the `q` key was pressed, break from the loop
    	if screen==0:
    	    os.system("echo 'q' >stop") #this simulates a keypress of the letter q which stops ffmpeg.  genius
    	    #https://stackoverflow.com/questions/9722624/how-to-stop-ffmpeg-remotely
    	    break

def MouseHandler(event, x, y, flags, param):
    global done, screen, img,tag
    
    if event==cv2.EVENT_LBUTTONUP and screen<6:
        if screen==5:
            screen=0
            img = cv2.imread('gui.png',1)
        elif (x>55 and x<168 and y>60 and y<145): #handle go live tap
            screen=4
            img = cv2.imread('confirm.png',1)
            img = cv2.putText(img, 'Start Streaming!?', (45, 130), cv2.FONT_HERSHEY_SIMPLEX,  
               1.5, (0, 0, 0), 7, cv2.LINE_AA)
            img = cv2.putText(img, 'Start Streaming!?', (45, 130), cv2.FONT_HERSHEY_SIMPLEX,  
               1.5, (255, 255, 255), 4, cv2.LINE_AA)
        elif (x>310 and x<418 and y>60 and y<145):
            if screen==0: #Handle tapped power button
                screen=1
                img = cv2.imread('confirm.png',1)
                img = cv2.putText(img, 'Turn Off Camera?', (30, 130), cv2.FONT_HERSHEY_SIMPLEX,  
                   1.5, (0, 0, 0), 7, cv2.LINE_AA)
                img = cv2.putText(img, 'Turn Off Camera?', (30, 130), cv2.FONT_HERSHEY_SIMPLEX,  
                   1.5, (255, 255, 255), 4, cv2.LINE_AA)  
            elif screen==1:
                screen=0
                img = cv2.imread('gui.png',1)
        elif (x>55 and x<168 and y>196 and y<280):
            if screen==0: #handle config youtube
                img = cv2.imread('confirm.png',1)
                img = cv2.putText(img, 'Change Your Stream Key?', (30, 130), cv2.FONT_HERSHEY_SIMPLEX,  
                   1, (0, 0, 0), 5, cv2.LINE_AA)
                img = cv2.putText(img, 'Change Your Stream Key?', (30, 130), cv2.FONT_HERSHEY_SIMPLEX,  
                   1, (255, 255, 255), 2, cv2.LINE_AA)   
                screen=2
            elif screen==1: #handle confirmed shutdown
                #os.system("sudo shutdown -h now")
                cv2.destroyAllWindows()
                exit()
            elif screen==2: #handle config youtube confirmed
                img = cv2.imread('gui.png',1)
                screen=0
            elif screen==3: #handle config wifi confirmed
                img = cv2.imread('gui.png',1)
                screen=0
            elif screen==4: #handle start streaming confirmed
                img = cv2.imread('gui.png',1)
                screen=5
                #os.system("ffmpeg -re -ar 44100 -ac 2 -acodec pcm_s16le -f s16le -ac 2 -i /dev/fb0 -f h264 -i - -vcodec copy -acodec aac -ab 128k -g 50 -strict experimental -f flv rtmp://a.rtmp.youtube.com/live2/628y-jagt-7b5c-4c9b &")
                StreamIt()
                screen=0
                img = cv2.imread('gui.png',1)
        elif (x>310 and x<418 and y>196 and y<280):
            if screen==0: #handle config wifi 
                img = cv2.imread('confirm.png',1)
                img = cv2.putText(img, 'Config WiFi?', (115, 130), cv2.FONT_HERSHEY_SIMPLEX,  
                    1.5, (0, 0, 0), 7, cv2.LINE_AA)
                img = cv2.putText(img, 'Config WiFi?', (115, 130), cv2.FONT_HERSHEY_SIMPLEX,  
                    1.5, (255, 255, 255), 4, cv2.LINE_AA)
                screen=3
            elif screen==1 or screen==2 or screen==3 or screen==4: #handle No
                img = cv2.imread('gui.png',1)
                screen=0
        cv2.imshow(tag,img)

done=False
screen=0
img = cv2.imread('gui.png',1)
tag="mywindow"

cv2.namedWindow(tag,0)
cv2.setWindowProperty(tag, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
cv2.imshow(tag,img)
cv2.setMouseCallback(tag, MouseHandler)
camera = PiCamera()
camera.resolution = (480, 320)
camera.framerate = 30
camera.rotation = 180
rawCapture = PiRGBArray(camera, size=(480, 320) )

while not done:
    k = cv2.waitKey(1)
    
cv2.destroyAllWindows()
exit()