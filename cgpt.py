import cv2
import matplotlib.pylab as plt


import time

vc = cv2.VideoCapture('videotestsrc ! video/x-raw,framerate=1/5 ! videoconvert ! appsink', cv2.CAP_GSTREAMER)

while True:
    start_t = time.time()
    status, image = vc.read()
    if not status:
        break
    end_t = time.time()
    print(f"time: {end_t-start_t}")

vc.release()

