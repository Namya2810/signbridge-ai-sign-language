import cv2
import numpy as np
import tensorflow as tf
import pickle
import time
import threading
import pyttsx3
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from faster_whisper import WhisperModel

# ─── 1. Model load ───────────────────────────────────────────────────────────
model = tf.keras.models.load_model("sign_model_grey.keras")
with open("label_encoder_grey.pkl", "rb") as f:
    le = pickle.load(f)
print("Sign model loaded.")

# ─── 2. TTS engine (Week 5) — ek baar banao, loop ke bahar ──────────────────
# pyttsx3 ko har baar init karna crash karta hai — isliye global engine
tts_engine = pyttsx3.init('sapi5')
tts_engine.setProperty('rate', 160)
tts_speaking = False       # flag: abhi speech chal rahi hai?
tts_enabled  = True        # toggle: user ne on/off kiya?

def speak_sentence(text):
    """
    Thread mein chalega taaki CV2 loop block na ho.
    pyttsx3 main thread pe hi kaam karta hai (Windows sapi5 limitation),
    isliye runAndWait() ko alag thread mein wrap karte hain.
    """
    global tts_speaking
    if not text.strip() or not tts_enabled:
        return
    tts_speaking = True
    tts_engine.say(text)
    tts_engine.runAndWait()
    tts_speaking = False

def trigger_tts(text):
    """Non-blocking TTS trigger."""
    if tts_speaking:
        return   # pehli wali khatam hone do
    threading.Thread(target=speak_sentence, args=(text,), daemon=True).start()

# ─── 3. Whisper model (Week 6) — heavy load, ek baar ───────────────────────
print("Whisper model load ho raha hai (pehli baar slow hoga)...")
whisper_model   = WhisperModel("small", compute_type="int8")
print("Whisper loaded.")

FS              = 16000          # sample rate (Whisper standard)
RECORD_SECONDS  = 6              # recording duration
stt_recording   = None           # numpy array — recorded audio
stt_status      = "idle"         # idle | recording | processing | done
stt_result      = ""             # transcribed text (dikhane ke liye)
mic_enabled     = True           # toggle

def do_recording():
    """6 seconds record karo."""
    global stt_recording, stt_status
    stt_status    = "recording"
    stt_recording = sd.rec(int(RECORD_SECONDS * FS), samplerate=FS,
                           channels=1, dtype='int16')
    sd.wait()
    stt_status = "processing"
    do_transcription()

def do_transcription():
    """Whisper se transcribe karo."""
    global stt_result, stt_status
    wav_write("recorded.wav", FS, stt_recording)
    segments, _ = whisper_model.transcribe(
        "recorded.wav",
        beam_size=5,
        temperature=0.0,
        vad_filter=True      # silence/noise filter
    )
    text = " ".join(seg.text for seg in segments).strip()
    stt_result = text if len(text) >= 2 else ""
    stt_status = "done"
    print(f"STT result: {stt_result}")

def start_stt():
    """Non-blocking STT trigger."""
    if stt_status == "recording" or not mic_enabled:
        return
    threading.Thread(target=do_recording, daemon=True).start()

# ─── 4. Webcam ───────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cv2.namedWindow("SignBridge - Week 5+6", cv2.WINDOW_NORMAL)
cv2.resizeWindow("SignBridge - Week 5+6", 800, 620)

# ─── 5. Settings ─────────────────────────────────────────────────────────────
ROI_TOP, ROI_LEFT     = 50, 400
ROI_BOTTOM, ROI_RIGHT = 280, 630
CONF_THRESHOLD        = 0.55
EDGE_THRESHOLD        = 0.008
STABILITY_TIME        = 1.0
SPACE_TIME            = 2.0

# ─── 6. Word Formation State (Week 4 — unchanged) ───────────────────────────
current_sentence  = ""
current_letter    = ""
stable_since      = None
last_hand_time    = time.time()
letter_just_added = False

frame_count  = 0
pred_letter  = ""
confidence   = 0.0
hand_present = False

print("Camera chal raha hai.")
print("Controls:")
print("  S = Speak sentence (TTS)")
print("  T = TTS on/off toggle")
print("  M = Mic record start (STT)")
print("  C = Clear sentence")
print("  Backspace = Delete last letter")
print("  Q = Quit")

# ─── 7. Main loop ─────────────────────────────────────────────────────────────
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    frame = cv2.flip(frame, 1)
    now = time.time()

    roi = frame[ROI_TOP:ROI_BOTTOM, ROI_LEFT:ROI_RIGHT]

    # ─── Hand detection ───────────────────────────────────────────────────
    roi_gray     = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges        = cv2.Canny(roi_gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    hand_present = edge_density > EDGE_THRESHOLD

    # ─── Predict (har 3rd frame) ──────────────────────────────────────────
    if hand_present and frame_count % 3 == 0:
        img = cv2.resize(roi, (64, 64))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img = img / 255.0
        img = np.expand_dims(img, axis=0)
        predictions = model.predict(img, verbose=0)
        confidence  = float(np.max(predictions))
        pred_letter = le.classes_[np.argmax(predictions)]

    # ─── Word Formation Logic (Week 4 — unchanged) ───────────────────────
    if hand_present and confidence >= CONF_THRESHOLD:
        last_hand_time    = now
        letter_just_added = False

        if pred_letter == current_letter:
            if stable_since is None:
                stable_since = now
            elif (now - stable_since) >= STABILITY_TIME and not letter_just_added:
                current_sentence  += pred_letter
                letter_just_added  = True
                stable_since       = now
                print(f"Letter added: {pred_letter} | Sentence: {current_sentence}")
        else:
            current_letter    = pred_letter
            stable_since      = None
            letter_just_added = False

    elif not hand_present:
        if (now - last_hand_time) >= SPACE_TIME and not letter_just_added:
            if current_sentence and not current_sentence.endswith(" "):
                current_sentence  += " "
                letter_just_added  = True
                print(f"Space added | Sentence: {current_sentence}")
        current_letter = ""
        stable_since   = None

    # ─── ROI box ─────────────────────────────────────────────────────────
    box_color = (0, 255, 0) if hand_present else (0, 0, 255)
    cv2.rectangle(frame, (ROI_LEFT, ROI_TOP), (ROI_RIGHT, ROI_BOTTOM), box_color, 2)
    cv2.putText(frame, "Hands Here",
                (ROI_LEFT, ROI_TOP - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 1)

    # ─── Prediction display ───────────────────────────────────────────────
    if hand_present and confidence >= CONF_THRESHOLD:
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

    # ─── Week 5: TTS status indicator (top-left) ──────────────────────────
    tts_color  = (0, 255, 0) if tts_enabled else (80, 80, 80)
    tts_label  = "SPK:ON " if tts_enabled else "SPK:OFF"
    if tts_speaking:
        tts_label = "SPEAKING"
        tts_color = (0, 200, 255)
    cv2.putText(frame, tts_label,
                (10, 160),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, tts_color, 1)

    # ─── Week 6: STT status indicator ────────────────────────────────────
    if stt_status == "recording":
        mic_label = "MIC: RECORDING..."
        mic_color = (0, 0, 255)
    elif stt_status == "processing":
        mic_label = "MIC: Processing..."
        mic_color = (0, 165, 255)
    elif stt_status == "done" and stt_result:
        mic_label = f"MIC: {stt_result[:30]}"
        mic_color = (0, 255, 0)
    else:
        mic_label = "MIC: M=Record"
        mic_color = (80, 80, 80)

    cv2.putText(frame, mic_label,
                (10, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, mic_color, 1)

    # ─── Edge debug ───────────────────────────────────────────────────────
    cv2.putText(frame, f"Edge: {edge_density:.3f}",
                (10, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    # ─── Sentence bottom bar ──────────────────────────────────────────────
    cv2.rectangle(frame, (0, 420), (640, 480), (30, 30, 30), -1)
    cv2.putText(frame, "Sentence:",
                (10, 445),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)

    display_sentence = current_sentence[-35:] if len(current_sentence) > 35 else current_sentence
    cv2.putText(frame, display_sentence,
                (100, 445),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.putText(frame, "S=Speak  T=TTS  M=Mic  C=Clear  BkSp=Del  Q=Quit",
                (10, 470),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (120, 120, 120), 1)

    # ─── Corner preview ───────────────────────────────────────────────────
    roi_preview = cv2.resize(roi, (100, 100))
    frame[10:110, 10:110] = roi_preview
    cv2.rectangle(frame, (10, 10), (110, 110), (255, 255, 0), 1)

    cv2.imshow("SignBridge - Week 5+6", frame)

    # ─── Keyboard controls ────────────────────────────────────────────────
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    elif key == ord('c'):
        current_sentence = ""
        stt_result       = ""
        stt_status       = "idle"
        print("Cleared.")

    elif key == 8:   # Backspace
        current_sentence = current_sentence[:-1]
        print(f"Backspace | Sentence: {current_sentence}")

    elif key == ord('s'):
        # Week 5: current sentence speak karo
        if current_sentence.strip():
            print(f"Speaking: {current_sentence}")
            trigger_tts(current_sentence.strip())
        else:
            print("Sentence empty — kuch sign karo pehle.")

    elif key == ord('t'):
        # Week 5: TTS toggle
        tts_enabled = not tts_enabled
        print(f"TTS {'enabled' if tts_enabled else 'disabled'}")

    elif key == ord('m'):
        # Week 6: mic recording start
        if stt_status not in ("recording", "processing"):
            stt_status = "idle"
            stt_result = ""
            print("Recording shuru ho rahi hai (6 seconds)...")
            start_stt()

# ─── Cleanup ─────────────────────────────────────────────────────────────────
cap.release()
cv2.destroyAllWindows()
tts_engine.stop()
print("Final sentence:", current_sentence)
