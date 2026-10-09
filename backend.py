"""Reliable FastAPI backend for SignBridge."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import pickle
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock, Thread
from typing import Any

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from recognition import PredictionSmoother, WordFormer, preprocess_frame

LOGGER = logging.getLogger("signbridge")
logging.basicConfig(level=os.getenv("SIGNBRIDGE_LOG_LEVEL", "INFO"))

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.getenv("SIGNBRIDGE_MODEL", BASE_DIR / "sign_model_grey.keras"))
ENCODER_PATH = Path(os.getenv("SIGNBRIDGE_ENCODER", BASE_DIR / "label_encoder_grey.pkl"))
MAX_FRAME_BYTES = 2_500_000


class Runtime:
    model: Any = None
    encoder: Any = None
    model_error: str | None = None
    input_size = (64, 64)
    predict_lock = Lock()
    state_lock = Lock()
    detector_lock = Lock()
    words = WordFormer()
    hand_detector: Any = None
    tts_lock = Lock()
    tts_busy = False
    stt_lock = Lock()
    stt_status = "idle"
    stt_result = ""
    stt_error = ""
    whisper: Any = None


runtime = Runtime()


def load_recognition_model() -> None:
    """Load model assets without making the whole API crash on failure."""
    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
        if not ENCODER_PATH.is_file():
            raise FileNotFoundError(f"Label encoder not found: {ENCODER_PATH}")

        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
        import tensorflow as tf

        runtime.model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        with ENCODER_PATH.open("rb") as handle:
            runtime.encoder = pickle.load(handle)

        shape = runtime.model.input_shape
        if not isinstance(shape, tuple) or len(shape) != 4:
            raise ValueError(f"Unsupported model input shape: {shape}")
        runtime.input_size = (int(shape[2]), int(shape[1]))
        output_classes = int(runtime.model.output_shape[-1])
        if output_classes != len(runtime.encoder.classes_):
            raise ValueError(
                f"Model has {output_classes} outputs but encoder has "
                f"{len(runtime.encoder.classes_)} classes"
            )
        runtime.model_error = None
        try:
            import mediapipe as mp

            runtime.hand_detector = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                min_detection_confidence=0.65,
                min_tracking_confidence=0.6,
            )
        except Exception:
            runtime.hand_detector = None
            LOGGER.exception("MediaPipe hand tracking is unavailable")
        LOGGER.info("Recognition model ready with %s classes", output_classes)
    except Exception as exc:
        runtime.model = None
        runtime.encoder = None
        runtime.model_error = str(exc)
        LOGGER.exception("Recognition model could not be loaded")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await asyncio.to_thread(load_recognition_model)
    yield


app = FastAPI(title="SignBridge API", version="3.0", lifespan=lifespan)
origins = os.getenv(
    "SIGNBRIDGE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in origins if origin.strip()],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class TextRequest(BaseModel):
    text: str


def locate_hand(frame: np.ndarray) -> tuple[np.ndarray, bool]:
    """Return a quality-checked crop containing every detected hand.

    Several bundled ISL reference signs use two hands. Cropping only the first
    hand removes important shape information and makes the CNN guess. Tiny or
    mostly off-frame detections are rejected before classification as well.
    """
    if runtime.hand_detector is None:
        # Never guess hand presence from generic image edges: faces, curtains,
        # and furniture otherwise become high-confidence false gestures.
        return frame, False

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    with runtime.detector_lock:
        result = runtime.hand_detector.process(rgb)
    if not result.multi_hand_landmarks:
        return frame, False

    height, width = frame.shape[:2]
    points = [
        point
        for hand_landmarks in result.multi_hand_landmarks
        for point in hand_landmarks.landmark
    ]
    xs = [point.x * width for point in points]
    ys = [point.y * height for point in points]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    box_width = x1 - x0
    box_height = y1 - y0
    box_area_ratio = (box_width * box_height) / max(width * height, 1)
    center_x = ((x0 + x1) / 2) / width
    center_y = ((y0 + y1) / 2) / height
    in_frame = sum(0 <= point.x <= 1 and 0 <= point.y <= 1 for point in points)
    quality_ok = (
        box_width >= width * 0.09
        and box_height >= height * 0.11
        and box_area_ratio >= 0.014
        and 0.16 <= center_x <= 0.84
        and 0.08 <= center_y <= 0.94
        and in_frame >= len(points) - 2
    )
    if not quality_ok:
        return frame, False

    side = max(box_width, box_height) * 1.7
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    left = max(int(cx - side / 2), 0)
    top = max(int(cy - side / 2), 0)
    right = min(int(cx + side / 2), width)
    bottom = min(int(cy + side / 2), height)
    return frame[top:bottom, left:right], right > left and bottom > top


def predict_probabilities(frame: np.ndarray) -> tuple[np.ndarray | None, bool]:
    hand_crop, hand_present = locate_hand(frame)
    if not hand_present:
        return None, False
    batch = preprocess_frame(hand_crop, runtime.input_size)
    with runtime.predict_lock:
        predictions = runtime.model.predict(batch, verbose=0)
    return np.asarray(predictions[0], dtype=np.float32), True


def decode_frame(data: str) -> np.ndarray:
    encoded = data.split(",", 1)[-1]
    try:
        raw = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise ValueError("Invalid base64 camera frame") from exc
    if not raw or len(raw) > MAX_FRAME_BYTES:
        raise ValueError("Camera frame is empty or too large")
    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Camera frame is not a valid image")
    return frame


def speak(text: str) -> None:
    try:
        import pyttsx3

        with runtime.tts_lock:
            runtime.tts_busy = True
            engine = pyttsx3.init()
            engine.setProperty("rate", 160)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
    except Exception:
        LOGGER.exception("Text-to-speech failed")
    finally:
        runtime.tts_busy = False


def record_and_transcribe() -> None:
    with runtime.stt_lock:
        try:
            import sounddevice as sd
            from faster_whisper import WhisperModel

            runtime.stt_status = "recording"
            audio = sd.rec(6 * 16_000, samplerate=16_000, channels=1, dtype="float32")
            sd.wait()
            runtime.stt_status = "processing"
            if runtime.whisper is None:
                runtime.whisper = WhisperModel(
                    os.getenv("SIGNBRIDGE_WHISPER_MODEL", "small"), compute_type="int8"
                )
            samples = audio.flatten()
            peak = float(np.max(np.abs(samples)))
            if peak > 1e-4:
                samples = samples * min(0.95 / peak, 8.0)
            segments, _ = runtime.whisper.transcribe(
                samples,
                language=os.getenv("SIGNBRIDGE_SPEECH_LANGUAGE", "en"),
                beam_size=5,
                temperature=0.0,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            runtime.stt_result = " ".join(s.text for s in segments).strip()
            runtime.stt_error = ""
            runtime.stt_status = "done"
        except Exception as exc:
            runtime.stt_error = str(exc)
            runtime.stt_status = "error"
            LOGGER.exception("Speech recognition failed")


@app.get("/status")
def status() -> dict:
    model_ready = runtime.model is not None and runtime.encoder is not None
    hand_tracking_ready = runtime.hand_detector is not None
    ready = model_ready and hand_tracking_ready
    return {
        "status": "online" if ready else "degraded",
        "recognition_ready": ready,
        "model_ready": model_ready,
        "hand_tracking_ready": hand_tracking_ready,
        "model": MODEL_PATH.name,
        "recognition_mode": "alphabet_static_cnn",
        "planned_mode": "30_frame_holistic_lstm_full_words",
        "classes": len(runtime.encoder.classes_) if ready else 0,
        "error": runtime.model_error,
    }


@app.post("/tts")
def tts(body: TextRequest) -> dict:
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Text cannot be empty")
    if runtime.tts_busy:
        raise HTTPException(status_code=409, detail="Text-to-speech is already running")
    Thread(target=speak, args=(text,), daemon=True).start()
    return {"ok": True, "speaking": text}


@app.post("/stt/start")
def stt_start() -> dict:
    if runtime.stt_status in {"recording", "processing"}:
        raise HTTPException(status_code=409, detail="Speech recognition is already running")
    runtime.stt_result = ""
    runtime.stt_error = ""
    Thread(target=record_and_transcribe, daemon=True).start()
    return {"ok": True, "status": "starting"}


@app.get("/stt/result")
def stt_result() -> dict:
    return {
        "status": runtime.stt_status,
        "result": runtime.stt_result,
        "error": runtime.stt_error,
    }


@app.websocket("/ws/predict")
async def websocket_predict(websocket: WebSocket) -> None:
    await websocket.accept()
    if runtime.model is None or runtime.encoder is None or runtime.hand_detector is None:
        message = runtime.model_error or "MediaPipe hand tracking is unavailable"
        await websocket.send_json({"type": "error", "message": message})
        await websocket.close(code=1013)
        return

    smoother = PredictionSmoother()
    try:
        while True:
            frame = decode_frame(await websocket.receive_text())
            probabilities, hand_present = await asyncio.to_thread(predict_probabilities, frame)
            if hand_present and probabilities is not None:
                index, confidence, margin = smoother.update(probabilities)
                letter = str(runtime.encoder.classes_[index])
            else:
                smoother.reset()
                letter, confidence, margin = "", 0.0, 0.0
            with runtime.state_lock:
                result = runtime.words.update(letter, confidence, margin, hand_present)
            result["type"] = "prediction"
            await websocket.send_json(result)
    except WebSocketDisconnect:
        LOGGER.info("Prediction client disconnected")
    except ValueError as exc:
        await websocket.send_json({"type": "error", "message": str(exc)})
        await websocket.close(code=1003)
    except Exception:
        LOGGER.exception("Prediction WebSocket failed")
        await websocket.close(code=1011)


@app.post("/clear")
def clear_hint() -> dict:
    with runtime.state_lock:
        runtime.words.clear()
    return {"ok": True, "sentence": ""}


@app.post("/backspace")
def backspace_hint() -> dict:
    with runtime.state_lock:
        sentence = runtime.words.backspace()
    return {"ok": True, "sentence": sentence}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=False)
