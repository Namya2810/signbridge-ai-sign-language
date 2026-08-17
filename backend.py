"""
SignBridge Backend — FastAPI + WebSocket
----------------------------------------
React frontend isse connect karta hai.
Endpoints:
  WS  /ws/predict   — camera frames aate hain, predictions jaate hain
  POST /tts          — sentence bhejo, TTS se bolwao
  POST /stt/start    — mic recording shuru karo
  GET  /stt/result   — transcription result lo
  GET  /status       — backend alive hai ya nahi
"""

import asyncio
import base64
import io
import pickle
import threading
import time

import cv2
import numpy as np
import pyttsx3
import sounddevice as sd
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from scipy.io.wavfile import write as wav_write
from faster_whisper import WhisperModel
import tensorflow as tf

# ─── App setup ───────────────────────────────────────────────────────────────
app = FastAPI(title="SignBridge API")

# React (localhost:5173) ko allow karo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Load CNN model ──────────────────────────────────────────────────────────
print("CNN model load ho raha hai...")
cnn_model = tf.keras.models.load_model("sign_model_grey.keras")
with open("label_encoder_grey.pkl", "rb") as f:
    le = pickle.load(f)
print(f"CNN model loaded. Classes: {len(le.classes_)}")

# ─── Load Whisper model ───────────────────────────────────────────────────────
print("Whisper model load ho raha hai (pehli baar slow hoga)...")
whisper_model = WhisperModel("small", compute_type="int8")
print("Whisper loaded.")

# ─── TTS engine ──────────────────────────────────────────────────────────────
tts_engine  = pyttsx3.init("sapi5")
tts_engine.setProperty("rate", 160)
tts_lock    = threading.Lock()
tts_busy    = False

def _speak(text: str):
    global tts_busy
    with tts_lock:
        tts_busy = True
        tts_engine.say(text)
        tts_engine.runAndWait()
        tts_busy = False

# ─── STT state ───────────────────────────────────────────────────────────────
FS             = 16000
RECORD_SECS    = 6
stt_status     = "idle"        # idle | recording | processing | done
stt_result     = ""
stt_audio      = None

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
    print(f"STT result: {stt_result}")

# ─── Word Formation state (same logic as week4) ──────────────────────────────
CONF_THRESHOLD  = 0.55
EDGE_THRESHOLD  = 0.015
STABILITY_TIME  = 2.0
SPACE_TIME      = 3.0

wf_state = {
    "current_sentence" : "",
    "current_letter"   : "",
    "stable_since"     : None,
    "last_hand_time"   : time.time(),
    "letter_just_added": False,
    "last_pred_letter" : "",
    "last_confidence"  : 0.0,
    "hand_present"     : False,
}

def process_frame(frame_bgr: np.ndarray) -> dict:
    """
    Ek frame lo, predict karo, word formation update karo.
    Returns dict jo frontend ko JSON mein bheja jayega.
    """
    s   = wf_state
    now = time.time()

    # ── Hand detection ────────────────────────────────────────────────────
    gray         = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    edges        = cv2.Canny(gray, 50, 150)
    edge_density = float(np.sum(edges > 0) / edges.size)
    hand_present = edge_density > EDGE_THRESHOLD
    s["hand_present"] = hand_present

    pred_letter = s["last_pred_letter"]
    confidence  = s["last_confidence"]

    # ── Predict ───────────────────────────────────────────────────────────
    if hand_present:
        img = cv2.resize(frame_bgr, (64, 64))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img = img / 255.0
        img = np.expand_dims(img, axis=0)
        preds       = cnn_model.predict(img, verbose=0)
        confidence  = float(np.max(preds))
        pred_letter = le.classes_[int(np.argmax(preds))]
        s["last_pred_letter"] = pred_letter
        s["last_confidence"]  = confidence

    # ── Word formation logic ──────────────────────────────────────────────
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
                print(f"Letter: {pred_letter} | Sentence: {s['current_sentence']}")
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

    # ── Progress bar value (0.0 – 1.0) ───────────────────────────────────
    progress = 0.0
    if s["stable_since"] and hand_present and confidence >= CONF_THRESHOLD:
        progress = min((now - s["stable_since"]) / STABILITY_TIME, 1.0)

    return {
        "hand_present"     : hand_present,
        "pred_letter"      : pred_letter if hand_present and confidence >= CONF_THRESHOLD else "",
        "confidence"       : round(confidence * 100, 1) if hand_present else 0,
        "current_sentence" : s["current_sentence"],
        "progress"         : round(progress, 3),
        "edge_density"     : round(edge_density, 4),
    }

# ─── HTTP endpoints ───────────────────────────────────────────────────────────

@app.get("/status")
def status():
    return {"status": "online", "model": "sign_model_grey", "classes": len(le.classes_)}


@app.post("/tts")
async def tts(body: dict):
    """Body: {"text": "HELLO WORLD"}"""
    text = body.get("text", "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "empty text"})
    if tts_busy:
        return JSONResponse({"ok": False, "error": "already speaking"})
    threading.Thread(target=_speak, args=(text,), daemon=True).start()
    return {"ok": True, "speaking": text}


@app.post("/stt/start")
async def stt_start():
    global stt_status, stt_result
    if stt_status == "recording":
        return {"ok": False, "error": "already recording"}
    stt_result = ""
    threading.Thread(target=_record_and_transcribe, daemon=True).start()
    return {"ok": True, "status": "recording"}


@app.get("/stt/result")
async def stt_result_endpoint():
    return {"status": stt_status, "result": stt_result}


@app.post("/clear")
async def clear_sentence():
    wf_state["current_sentence"]   = ""
    wf_state["current_letter"]     = ""
    wf_state["stable_since"]       = None
    wf_state["letter_just_added"]  = False
    return {"ok": True}


@app.post("/backspace")
async def backspace():
    s = wf_state
    if s["current_sentence"]:
        s["current_sentence"] = s["current_sentence"][:-1]
    return {"ok": True, "sentence": s["current_sentence"]}


# ─── WebSocket — main prediction loop ────────────────────────────────────────
@app.websocket("/ws/predict")
async def websocket_predict(ws: WebSocket):
    """
    Frontend se base64 JPEG frames aate hain.
    Backend prediction + sentence state JSON mein bhejta hai.
    """
    await ws.accept()
    print("WebSocket connected.")
    frame_count = 0

    try:
        while True:
            data = await ws.receive_text()

            # base64 decode → numpy array
            header, encoded = data.split(",", 1)
            img_bytes = base64.b64decode(encoded)
            np_arr    = np.frombuffer(img_bytes, np.uint8)
            frame     = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            frame_count += 1

            # Har 3rd frame pe predict (same as week3/4)
            if frame_count % 3 == 0:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, process_frame, frame
                )
                await ws.send_json(result)

    except WebSocketDisconnect:
        print("WebSocket disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")


# ─── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=False)
