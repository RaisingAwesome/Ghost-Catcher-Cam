import cv2
import os

os.putenv('SDL_VIDEODRIVER','fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

done=False
screen=0
img = cv2.imread('gui.png',1)
tag="mywindow"

def MouseHandler(event, x, y, flags, param):
    global done, screen, img,tag
    
    if event==cv2.EVENT_LBUTTONUP:
        if (x>55 and x<168 and y>60 and y<145): #handle go live tap
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
                cv2.destroyAllWindows()
                os.system("sudo raspivid -o - -t 0 -vf -hf -w 1280 -h 720 -fps 25 -b 4000000 -g 50 | ffmpeg -re -ar 44100 -ac 2 -acodec pcm_s16le -f s16le -ac 2 -i /dev/zero -f h264 -i - -vcodec copy -acodec aac -ab 128k -g 50 -strict experimental -f flv rtmp://a.rtmp.youtube.com/live2/628y-jagt-7b5c-4c9b &")
                while True:
                    k = cv2.waitKey(1)
                
                screen=0
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
cv2.namedWindow(tag,0)
cv2.setWindowProperty(tag, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);
cv2.imshow(tag,img)
cv2.setMouseCallback(tag, MouseHandler)

while not done:
    
    k = cv2.waitKey(1)

if k == 27:         # wait for ESC key to exit
    cv2.destroyAllWindows()
    
elif k == ord('s'): # wait for 's' key to save and exit
    cv2.imwrite('messigray.png',img)
    cv2.destroyAllWindows()