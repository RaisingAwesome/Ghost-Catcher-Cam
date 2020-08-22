ffmpeg -f lavfi -i anullsrc -loop 1 -i exit.png -vcodec libx264 -pix_fmt yuv420p -f flv "rtmp://a.rtmp.youtube.com/live2/628y-jagt-7b5c-4c9b"

