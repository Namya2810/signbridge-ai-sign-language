"""
collect_data.py — MediaPipe se landmark data collect karo
----------------------------------------------------------
Har letter ke liye 100 samples collect karo webcam se.
Press SPACE to capture a sample, Q to quit current letter.
Data save hoga: landmark_data/ folder mein CSV files.
"""

import cv2
import mediapipe as mp
import numpy as np
import csv
import os
import time

# ─── MediaPipe setup ─────────────────────────────────────────────────────────
mp_hands    = mp.solutions.hands
mp_drawing  = mp.solutions.drawing_utils
hands       = mp_hands.Hands(
    static_image_mode       = False,
    max_num_hands           = 1,
    min_detection_confidence= 0.7,
    min_tracking_confidence = 0.5
)

# ─── Classes — ISL 36 classes ─────────────────────────────────────────────────
CLASSES = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + list("0123456789")
SAMPLES_PER_CLASS = 100

# ─── Output folder ────────────────────────────────────────────────────────────
os.makedirs("landmark_data", exist_ok=True)
DATA_FILE = "landmark_data/landmarks.csv"

# Header: 21 landmarks × 3 (x,y,z) = 63 features + label
HEADER = [f"{axis}{i}" for i in range(21) for axis in ["x","y","z"]] + ["label"]

# Load existing data to resume if interrupted
existing_counts = {}
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = row["label"]
            existing_counts[label] = existing_counts.get(label, 0) + 1
    print("Existing data found:")
    for cls, cnt in sorted(existing_counts.items()):
        print(f"  {cls}: {cnt} samples")
else:
    # Write header
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)

# ─── Webcam ───────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cv2.namedWindow("Data Collection", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Data Collection", 800, 600)

def extract_landmarks(results):
    """21 landmarks se 63 features nikalo (normalized)."""
    if not results.multi_hand_landmarks:
        return None
    hand = results.multi_hand_landmarks[0]
    # Wrist ko origin banao (normalize)
    wrist_x = hand.landmark[0].x
    wrist_y = hand.landmark[0].y
    wrist_z = hand.landmark[0].z
    features = []
    for lm in hand.landmark:
        features.extend([
            lm.x - wrist_x,
            lm.y - wrist_y,
            lm.z - wrist_z,
        ])
    return features

print("\n=== DATA COLLECTION SHURU ===")
print("SPACE = sample lo | Q = agla letter | ESC = quit")
print("Auto-capture mode: haath steady rakho, automatic capture hoga!\n")

for cls in CLASSES:
    already = existing_counts.get(cls, 0)
    if already >= SAMPLES_PER_CLASS:
        print(f"[SKIP] {cls} — already {already} samples")
        continue

    needed   = SAMPLES_PER_CLASS - already
    collected = 0
    last_capture_time = 0
    AUTO_INTERVAL = 0.5  # har 0.5 second mein auto-capture

    print(f"\n>>> Letter: {cls} | Needed: {needed} more samples")
    print(f"    Haath stable rakho — auto-capture every 0.5s")

    while collected < needed:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        # Draw landmarks
        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame, hand_lms, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=3),
                    mp_drawing.DrawingSpec(color=(0,180,0), thickness=2)
                )

        # Auto-capture
        features = extract_landmarks(results)
        now = time.time()
        if features and (now - last_capture_time) >= AUTO_INTERVAL:
            with open(DATA_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(features + [cls])
            collected += 1
            last_capture_time = now

        # UI
        progress = int((collected / needed) * 300)
        cv2.rectangle(frame, (20, 20), (320, 50), (50,50,50), -1)
        cv2.rectangle(frame, (20, 20), (20 + progress, 50), (0,255,100), -1)

        # Letter display
        cv2.rectangle(frame, (0, 60), (640, 140), (20,20,20), -1)
        cv2.putText(frame, f"Letter: {cls}",
                    (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 2.5,
                    (0, 255, 150), 4)

        cv2.putText(frame, f"{collected}/{needed} samples",
                    (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (200,200,200), 2)

        if features:
            cv2.putText(frame, "Hand detected — capturing",
                        (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0,255,0), 1)
        else:
            cv2.putText(frame, "NO HAND — show your hand",
                        (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0,0,255), 1)

        cv2.putText(frame, "Q=skip letter | ESC=quit",
                    (20, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (100,100,100), 1)

        cv2.imshow("Data Collection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:   # ESC
            print("Quit!")
            cap.release()
            cv2.destroyAllWindows()
            exit()
        elif key == ord('q'):
            print(f"  Skipped {cls} with {collected} samples")
            break

    if collected > 0:
        print(f"  ✓ {cls}: {collected} samples collected")

cap.release()
cv2.destroyAllWindows()
hands.close()
print("\n=== DATA COLLECTION COMPLETE ===")
print(f"Data saved to: {DATA_FILE}")
print("Ab train_classifier.py chalao!")
