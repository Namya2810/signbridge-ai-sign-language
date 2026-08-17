import cv2
import numpy as np
import tensorflow as tf
import pickle
import time

# ─── 1. Model load ───────────────────────────────────────────────────────────
model = tf.keras.models.load_model("sign_model_grey.keras")
with open("label_encoder_grey.pkl", "rb") as f:
    le = pickle.load(f)
print("Model loaded.")

# ─── 2. Webcam ───────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cv2.namedWindow("SignBridge - Week 4", cv2.WINDOW_NORMAL)
cv2.resizeWindow("SignBridge - Week 4", 800, 600)

# ─── 3. Settings ─────────────────────────────────────────────────────────────
ROI_TOP, ROI_LEFT     = 50, 400
ROI_BOTTOM, ROI_RIGHT = 280, 630
CONF_THRESHOLD        = 0.55
EDGE_THRESHOLD        = 0.008
STABILITY_TIME        = 1.0    # 1 second same letter = accept
SPACE_TIME            = 2.0    # 2 second no hand = space

# ─── 4. Word Formation State ─────────────────────────────────────────────────
current_sentence   = ""        # poora sentence
current_letter     = ""        # abhi jo predict ho raha hai
stable_since       = None      # kab se same letter aa raha hai
last_accepted      = ""        # last accepted letter (duplicate avoid)
last_hand_time     = time.time()
letter_just_added  = False

frame_count  = 0
pred_letter  = ""
confidence   = 0.0
hand_present = False

print("Camera chal raha hai.")
print("Controls: C = clear | BACKSPACE = last letter hatao | Q = quit")

# ─── 5. Main loop ─────────────────────────────────────────────────────────────
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    frame = cv2.flip(frame, 1)

    roi = frame[ROI_TOP:ROI_BOTTOM, ROI_LEFT:ROI_RIGHT]

    # ─── 6. Hand detection ───────────────────────────────────────────────────
    roi_gray     = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges        = cv2.Canny(roi_gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    hand_present = edge_density > EDGE_THRESHOLD

    # ─── 7. Predict ──────────────────────────────────────────────────────────
    if hand_present and frame_count % 3 == 0:
        img = cv2.resize(roi, (64, 64))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)   # greyscale convert
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)   # 3 channel wapas
        img = img / 255.0
        img = np.expand_dims(img, axis=0)
        predictions = model.predict(img, verbose=0)
        confidence  = float(np.max(predictions))
        pred_letter = le.classes_[np.argmax(predictions)]

    # ─── 8. Word Formation Logic ─────────────────────────────────────────────
    now = time.time()

    if hand_present and confidence >= CONF_THRESHOLD:
        last_hand_time = now
        letter_just_added = False

        if pred_letter == current_letter:
            # Same letter aa raha hai — stability timer check karo
            if stable_since is None:
                stable_since = now
            elif (now - stable_since) >= STABILITY_TIME and not letter_just_added:
                # 1 second ho gaya — letter accept karo
                current_sentence += pred_letter
                letter_just_added = True
                stable_since = now    # reset for next letter
                print(f"Letter added: {pred_letter} | Sentence: {current_sentence}")
        else:
            # Letter badla — timer reset karo
            current_letter = pred_letter
            stable_since   = None
            letter_just_added = False

    elif not hand_present:
        # Haath nahi hai
        if (now - last_hand_time) >= SPACE_TIME and not letter_just_added:
            if current_sentence and not current_sentence.endswith(" "):
                current_sentence += " "
                print(f"Space added | Sentence: {current_sentence}")
                letter_just_added = True
        current_letter = ""
        stable_since   = None

    # ─── 9. ROI box draw ─────────────────────────────────────────────────────
    box_color = (0, 255, 0) if hand_present else (0, 0, 255)
    cv2.rectangle(frame, (ROI_LEFT, ROI_TOP), (ROI_RIGHT, ROI_BOTTOM), box_color, 2)
    cv2.putText(frame, "Hands Here",
                (ROI_LEFT, ROI_TOP - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1)

    # ─── 10. Current prediction display ──────────────────────────────────────
    if hand_present and confidence >= CONF_THRESHOLD:
        # Stability progress bar
        if stable_since:
            elapsed  = min(now - stable_since, STABILITY_TIME)
            progress = int((elapsed / STABILITY_TIME) * (ROI_RIGHT - ROI_LEFT))
            cv2.rectangle(frame,
                          (ROI_LEFT, ROI_BOTTOM + 5),
                          (ROI_LEFT + progress, ROI_BOTTOM + 15),
                          (0, 255, 255), -1)
            cv2.rectangle(frame,
                          (ROI_LEFT, ROI_BOTTOM + 5),
                          (ROI_RIGHT, ROI_BOTTOM + 15),
                          (100, 100, 100), 1)

        label = f"{pred_letter}  {confidence*100:.0f}%"
        cv2.rectangle(frame,
                      (ROI_LEFT, ROI_TOP + 5),
                      (ROI_LEFT + 160, ROI_TOP + 35),
                      (0, 0, 0), -1)
        cv2.putText(frame, label,
                    (ROI_LEFT + 5, ROI_TOP + 27),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "-- --",
                    (ROI_LEFT + 5, ROI_TOP + 27),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 1)

    # ─── 11. Sentence display (bottom bar) ───────────────────────────────────
    cv2.putText(frame, f"Edge: {edge_density:.3f}", (10, 390),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)
    cv2.rectangle(frame, (0, 420), (640, 480), (30, 30, 30), -1)
    cv2.putText(frame, "Sentence:",
                (10, 445),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    # Sentence ko right side se trim karo agar bahut lamba ho
    display_sentence = current_sentence[-35:] if len(current_sentence) > 35 else current_sentence
    cv2.putText(frame, display_sentence,
                (100, 445),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.putText(frame, "C=Clear  BkSp=Delete  Q=Quit",
                (10, 470),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)

    # ─── 12. Corner preview ──────────────────────────────────────────────────
    roi_preview = cv2.resize(roi, (100, 100))
    frame[10:110, 10:110] = roi_preview
    cv2.rectangle(frame, (10, 10), (110, 110), (255, 255, 0), 1)

    cv2.imshow("SignBridge - Week 4", frame)

    # ─── 13. Keyboard controls ───────────────────────────────────────────────
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        current_sentence = ""
        print("Sentence cleared.")
    elif key == 8:  # Backspace
        current_sentence = current_sentence[:-1]
        print(f"Backspace | Sentence: {current_sentence}")

cap.release()
cv2.destroyAllWindows()
print("Final sentence:", current_sentence)