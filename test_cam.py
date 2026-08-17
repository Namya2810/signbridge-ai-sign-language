import cv2
for i in range(3):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera mila at index {i}")
        cap.release()
    else:
        print(f"Index {i} — nahi mila")