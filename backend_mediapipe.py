"""
SignBridge Backend — FastAPI + WebSocket + MediaPipe
----------------------------------------------------
MediaPipe se haath ke 21 landmarks extract karta hai.
Random Forest classifier se letter predict karta hai.
"""

import asyncio
import base64
import pickle
import threading
import time

import cv2
import mediapipe as mp
import numpy as np
import pyttsx3
import sounddevice as sd
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from scipy.io.wavfile import write as wav_write
from faster_whisper import WhisperModel

# ─── App setup ───────────────────────────────────────────────────────────────
app = FastAPI(title="SignBridge API — MediaPipe")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── MediaPipe Hands ──────────────────────────────────────────────────────────
mp_hands   = mp.solutions.hands
hands_detector = mp_hands.Hands(
    static_image_mode        = False,
    max_num_hands            = 1,
    min_detection_confidence = 0.7,
    min_tracking_confidence  = 0.5
)
print("MediaPipe Hands loaded.")

# ─── Landmark Classifier ──────────────────────────────────────────────────────
print("Landmark classifier load ho raha hai...")
with open("landmark_classifier.pkl", "rb") as f:
    clf = pickle.load(f)
with open("landmark_encoder.pkl", "rb") as f:
    le = pickle.load(f)
print(f"Classifier loaded. Classes: {len(le.classes_)}")

# ─── Whisper ─────────────────────────────────────────────────────────────────
print("Whisper load ho raha hai...")
whisper_model = WhisperModel("small", compute_type="int8")
print("Whisper loaded.")

# ─── TTS ──────────────────────────────────────────────────────────────────────
tts_engine = pyttsx3.init("sapi5")
tts_engine.setProperty("rate", 160)
tts_lock   = threading.Lock()
tts_busy   = False

def _speak(text: str):
    global tts_busy
    with tts_lock:
        tts_busy = True
        tts_engine.say(text)
        tts_engine.runAndWait()
        tts_busy = False

# ─── STT ──────────────────────────────────────────────────────────────────────
FS           = 16000
RECORD_SECS  = 6
stt_status   = "idle"
stt_result   = ""
stt_audio    = None

def _record_and_transcribe():
    global stt_status, stt_result, stt_audio
    stt_status = "recording"
    stt_audio  = sd.rec(int(RECORD_SECS * FS), samplerate=FS,
                        channels=1, dtype="int16")
    sd.wait()
    stt_status = "processing"
    wav_write("recorded.wav", FS, stt_audio)
    segments, _ = whisper_model.transcribe(
        "recorded.wav", beam_size=5, temperature=0.0, vad_filter=True
    )
    text = " ".join(s.text for s in segments).strip()
    stt_result = text if len(text) >= 2 else ""
    stt_status = "done"
    print(f"STT: {stt_result}")

# ─── Word Formation ───────────────────────────────────────────────────────────
CONF_THRESHOLD = 0.6    # Random Forest probability threshold
STABILITY_TIME = 1.5
SPACE_TIME     = 2.5

wf = {
    "current_sentence" : "",
    "current_letter"   : "",
    "stable_since"     : None,
    "last_hand_time"   : time.time(),
    "letter_just_added": False,
    "last_pred_letter" : "",
    "last_confidence"  : 0.0,
    "hand_present"     : False,
}

def extract_landmarks(frame_bgr):
    """MediaPipe se 63 features nikalo (wrist-normalized x,y,z × 21)."""
    rgb     = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    results = hands_detector.process(rgb)

    if not results.multi_hand_landmarks:
        return None, None

    hand    = results.multi_hand_landmarks[0]
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
    return np.array(features), results

def process_frame(frame_bgr: np.ndarray) -> dict:
    s   = wf
    now = time.time()

    features, mp_results = extract_landmarks(frame_bgr)
    hand_present = features is not None
    s["hand_present"] = hand_present

    pred_letter = s["last_pred_letter"]
    confidence  = s["last_confidence"]

    if hand_present:
        proba       = clf.predict_proba([features])[0]
        confidence  = float(np.max(proba))
        pred_letter = le.classes_[int(np.argmax(proba))]
        s["last_pred_letter"] = pred_letter
        s["last_confidence"]  = confidence

    # Word formation logic
    if hand_present and confidence >= CONF_THRESHOLD:
        s["last_hand_time"]    = now
        s["letter_just_added"] = False

        if pred_letter == s["current_letter"]:
            if s["stable_since"] is None:
                s["stable_since"] = now
            elif (now - s["stable_since"]) >= STABILITY_TIME and not s["letter_just_added"]:
                s["current_sentence"]  += pred_letter
                s["letter_just_added"]  = True
                s["stable_since"]       = now
                print(f"Letter: {pred_letter} ({confidence*100:.0f}%) | {s['current_sentence']}")
        else:
            s["current_letter"]    = pred_letter
            s["stable_since"]      = None
            s["letter_just_added"] = False

    elif not hand_present:
        if (now - s["last_hand_time"]) >= SPACE_TIME and not s["letter_just_added"]:
            if s["current_sentence"] and not s["current_sentence"].endswith(" "):
                s["current_sentence"]  += " "
                s["letter_just_added"]  = True
        s["current_letter"] = ""
        s["stable_since"]   = None

    progress = 0.0
    if s["stable_since"] and hand_present and confidence >= CONF_THRESHOLD:
        progress = min((now - s["stable_since"]) / STABILITY_TIME, 1.0)

    return {
        "hand_present"     : hand_present,
        "pred_letter"      : pred_letter if hand_present and confidence >= CONF_THRESHOLD else "",
        "confidence"       : round(confidence * 100, 1) if hand_present else 0,
        "current_sentence" : s["current_sentence"],
        "progress"         : round(progress, 3),
    }

# ─── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/status")
def status():
    return {"status": "online", "model": "mediapipe_rf", "classes": len(le.classes_)}

@app.post("/tts")
async def tts(body: dict):
    text = body.get("text", "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty"})
    if tts_busy:
        return JSONResponse({"ok": False, "error": "busy"})
    threading.Thread(target=_speak, args=(text,), daemon=True).start()
    return {"ok": True}

@app.post("/stt/start")
async def stt_start():
    global stt_status, stt_result
    if stt_status == "recording":
        return {"ok": False, "error": "already recording"}
    stt_result = ""
    threading.Thread(target=_record_and_transcribe, daemon=True).start()
    return {"ok": True}

@app.get("/stt/result")
async def stt_result_ep():
    return {"status": stt_status, "result": stt_result}

@app.post("/clear")
async def clear():
    for k in ["current_sentence","current_letter","stable_since","letter_just_added"]:
        wf[k] = "" if k != "stable_since" and k != "letter_just_added" else (None if k == "stable_since" else False)
    return {"ok": True}

@app.post("/backspace")
async def backspace():
    if wf["current_sentence"]:
        wf["current_sentence"] = wf["current_sentence"][:-1]
    return {"ok": True, "sentence": wf["current_sentence"]}

@app.websocket("/ws/predict")
async def ws_predict(ws: WebSocket):
    await ws.accept()
    print("WS connected.")
    frame_count = 0
    try:
        while True:
            data   = await ws.receive_text()
            _, enc = data.split(",", 1)
            arr    = np.frombuffer(base64.b64decode(enc), np.uint8)
            frame  = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                continue
            frame_count += 1
            if frame_count % 3 == 0:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, process_frame, frame
                )
                await ws.send_json(result)
    except WebSocketDisconnect:
        print("WS disconnected.")
    except Exception as e:
        print(f"WS error: {e}")

if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=False)
