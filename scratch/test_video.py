import cv2
import os

video_file = "KhaNgan.MOV"
cap = cv2.VideoCapture(video_file)
if cap.isOpened():
    print(f"SUCCESS: Opened {video_file}")
    ret, frame = cap.read()
    if ret:
        print(f"SUCCESS: Read first frame of {video_file}")
    else:
        print(f"FAILED: Could not read first frame of {video_file}")
    cap.release()
else:
    print(f"FAILED: Could not open {video_file}")
