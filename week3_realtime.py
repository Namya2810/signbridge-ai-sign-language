import cv2
import numpy as np
import tensorflow as tf
import pickle
import time

# ─── 1. Model load ───────────────────────────────────────────────────────────
model = tf.keras.models.load_model("sign_model_grey.keras")
with open("label_encoder_grey.pkl", "rb") as f:
    le = pickle.load(f)
print("Model loaded. Classes:", le.classes_)

# ─── 2. Webcam ───────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("ERROR: Webcam nahi mila")
    exit()

# ─── 3. Settings ─────────────────────────────────────────────────────────────
ROI_TOP, ROI_LEFT     = 50, 400
ROI_BOTTOM, ROI_RIGHT = 280, 630
CONF_THRESHOLD        = 0.55
EDGE_THRESHOLD        = 0.008 # Hand detection ke liye edge density threshold

# ─── 4. State variables ───────────────────────────────────────────────────────
frame_count  = 0
pred_letter  = ""
confidence   = 0.0
hand_present = False

print("Camera chal raha hai. Q dabao band karne ke liye.")

cv2.namedWindow("SignBridge - Week 3", cv2.WINDOW_NORMAL)
cv2.resizeWindow("SignBridge - Week 3", 720, 560)

# ─── 5. Main loop ─────────────────────────────────────────────────────────────
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    frame = cv2.flip(frame, 1)

    # ROI extract
    roi = frame[ROI_TOP:ROI_BOTTOM, ROI_LEFT:ROI_RIGHT]

    # ─── 6. Hand detection ───────────────────────────────────────────────────
    roi_gray     = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges        = cv2.Canny(roi_gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    hand_present = edge_density > EDGE_THRESHOLD

    # ─── 7. Predict (har 3rd frame) ──────────────────────────────────────────
    if hand_present and frame_count % 3 == 0:
        img = cv2.resize(roi, (64, 64))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)   # greyscale convert
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)   # 3 channel wapas
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        predictions = model.predict(img, verbose=0)
        confidence  = float(np.max(predictions))
        pred_letter = le.classes_[np.argmax(predictions)]

    # ─── 8. ROI box draw ─────────────────────────────────────────────────────
    box_color = (0, 255, 0) if hand_present else (0, 0, 255)
    cv2.rectangle(frame,
                  (ROI_LEFT, ROI_TOP),
                  (ROI_RIGHT, ROI_BOTTOM),
                  box_color, 2)

    cv2.putText(frame, "Haath yahan rakhein",
                (ROI_LEFT, ROI_TOP - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 1)

    # ─── 9. Prediction display ───────────────────────────────────────────────
    if not hand_present:
        label = "-- haath nahi --"
        color = (100, 100, 100)
    elif confidence >= CONF_THRESHOLD:
        label = f"{pred_letter}   {confidence*100:.1f}%"
        color = (0, 255, 0)
    else:
        label = f"?   {confidence*100:.1f}%"
        color = (0, 165, 255)

    # Text background box taaki readable rahe
    text_y = ROI_TOP + 30
    cv2.rectangle(frame,
                  (ROI_LEFT + 5, text_y - 25),
                  (ROI_LEFT + 280, text_y + 10),
                  (0, 0, 0), -1)
    cv2.putText(frame, label,
                (ROI_LEFT + 10, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    # Edge density debug info
    cv2.putText(frame,
                f"Edge: {edge_density:.3f}",
                (10, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # ─── 10. Corner preview ──────────────────────────────────────────────────
    roi_preview = cv2.resize(roi, (120, 120))
    frame[10:130, 10:130] = roi_preview
    cv2.rectangle(frame, (10, 10), (130, 130), (255, 255, 0), 1)
    cv2.putText(frame, "Model input",
                (10, 148),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)

    cv2.imshow("SignBridge - Week 3", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Camera is shutting down.")