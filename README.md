# SignBridge — AI Sign Language Translator

SignBridge is a multimodal accessibility application for real-time sign-language recognition, word formation, text-to-speech, and speech-to-text. A React dashboard streams webcam frames to a FastAPI WebSocket backend, where a trained CNN recognizes hand signs.

## Features

- Real-time webcam sign recognition over WebSockets
- Trained TensorFlow/Keras sign classifiers
- Letter-to-word formation with confidence scores
- Text-to-speech output
- Whisper-based speech-to-text
- Responsive React dashboard
- Dataset collection and model-training utilities

## Architecture

```text
React + webcam -> WebSocket -> FastAPI -> TensorFlow model
                                      -> recognized text -> TTS
Microphone -> Faster Whisper -> speech transcript
```

## Run locally

### Backend

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python backend.py
```

The API starts at `http://localhost:8000`.

### Frontend

```bash
cd ui
npm install
npm run dev
```

Open `http://localhost:5173` and allow camera/microphone access.

## Models

The repository includes the trained CNN model and label encoder needed by `backend.py`. `backend_mediapipe.py` is an experimental landmark-classifier variant and requires separately trained `landmark_classifier.pkl` and `landmark_encoder.pkl` artifacts.

## Notes

The first backend launch downloads the Faster Whisper `small` model. Windows SAPI is used by the included text-to-speech configuration.
