# SignBridge

SignBridge is a local Indian Sign Language assistant. A React camera interface sends frames to a FastAPI backend, which recognizes letters, forms words, converts signed text to speech, and can transcribe spoken audio for sign-reference playback.

## Current status versus the final plan

The included `sign_model_grey.keras` is a static 36-class alphabet/number CNN. It is **Phase 1**, not the final dynamic-word model described in the project write-up. The interface labels this honestly as **Alphabet prototype**.

The final documented target is a privacy-first, bi-directional conversation system using MediaPipe Holistic landmarks and a 30-frame LSTM sequence model for full-word gestures. Completing that phase requires collecting labelled landmark sequences and training/exporting a new sequence model; those sequence datasets and models are not part of this repository yet.

## What was improved

- MediaPipe hand-landmark gating and cropping; prediction is paused when no real hand is detected
- Seven-frame probability smoothing and top-class confidence-margin filtering
- Stable-letter acceptance that prevents accidental repeated characters
- Per-pause spacing, clear, and backspace controls
- Model paths resolved from the project folder with shape/class validation
- Lazy loading for speech recognition and text-to-speech
- Graceful degraded backend status instead of startup crashes
- Responsive camera, dashboard, status, and touch-friendly controls

## Requirements

- Windows 10 or 11
- Python 3.12 (64-bit)
- Node.js 20 or newer
- Webcam and microphone permissions

The included model expects `64 × 64 × 3` images and produces 36 classes (A–Z and 0–9).

## First-time setup

Open PowerShell in this folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
```

The setup creates `.venv`, installs Python packages, and installs the frontend packages.

## Start the application

```powershell
.\scripts\start.ps1
```

Then open `http://127.0.0.1:5173`. Keep the backend window open while using the app.

You can also launch the two services separately:

```powershell
.\scripts\start-backend.ps1
.\scripts\start-frontend.ps1
```

## Recognition tips

1. Use an evenly lit background with your hand clearly separated from it.
2. Keep one hand inside the on-screen guide.
3. Hold a sign steadily until the progress indicator completes.
4. Change or briefly lower your hand before signing the same letter twice.
5. Lower your hand briefly to insert a space.
6. Lower your hand for five seconds to complete the draft automatically, or use **Complete & Speak** immediately.

## Conversation flow

- Camera gestures build a live draft beside the video.
- **Complete & Speak** adds the draft as a signed-message chat bubble and reads it aloud.
- A five-second no-hand pause completes the same action automatically.
- **Speak** records a six-second microphone message and adds the transcription as a spoken-message bubble.
- The sign playback panel shows that spoken message character-by-character at one-second intervals and loops until it is closed or replaced by the next spoken message.

## Configuration

Copy `.env.example` values into your shell environment when custom paths or settings are needed. Copy `ui/.env.example` to `ui/.env` to point the interface at a backend on another host.

The backend health endpoint is `http://127.0.0.1:8000/status`. A `degraded` response includes the model-loading error so setup problems are visible without crashing the server.

## Project layout

- `backend.py` — API, WebSocket, model lifecycle, speech features
- `recognition.py` — image preprocessing, temporal smoothing, word formation
- `ui/` — React and Vite interface
- `tools/` — optional landmark data collection and classifier training
- `docs/` — project plan and original write-up
- `tests/` — recognition state-machine tests
- `scripts/` — setup and launch scripts
- `sign_model_grey.keras` / `label_encoder_grey.pkl` — active recognition assets
- `isl_dataset/` — local-only training images (about 2.4 GB, 90,000 files; not committed, see `.gitignore`). `tools/train_classifier.py` expects it when retraining.
