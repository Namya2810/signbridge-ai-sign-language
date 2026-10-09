import { useCallback, useEffect, useRef, useState } from "react";
import Navbar from "../components/Navbar";
import CameraFeed from "../components/CameraFeed";
import ChatPanel from "../components/ChatPanel";
import Controls from "../components/Controls";
import SignDisplay from "../components/SignDisplay";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const AUTO_COMPLETE_MS = 5000;

export default function Dashboard() {
  const [prediction, setPrediction] = useState(null);
  const [connection, setConnection] = useState("connecting");
  const [messages, setMessages] = useState([]);
  const [signPlayback, setSignPlayback] = useState(null);
  const [autoCompleteAt, setAutoCompleteAt] = useState(null);
  const completingRef = useRef(false);
  const sentence = prediction?.current_sentence ?? "";
  const draft = sentence.trim();

  const handlePrediction = useCallback((result) => {
    setPrediction(result);
    const hasDraft = Boolean(result.current_sentence?.trim());
    if (!result.hand_present && hasDraft) {
      setAutoCompleteAt((current) => current ?? Date.now() + AUTO_COMPLETE_MS);
    } else {
      setAutoCompleteAt(null);
    }
  }, []);

  const clearBackendDraft = useCallback(async () => {
    const response = await fetch(`${API}/clear`, { method: "POST" });
    if (!response.ok) throw new Error("Could not clear the live draft");
    setPrediction((previous) => ({ ...(previous || {}), current_sentence: "" }));
  }, []);

  const speak = useCallback(async (text) => {
    const response = await fetch(`${API}/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!response.ok) throw new Error("Speech playback could not start");
  }, []);

  const completeDraft = useCallback(async () => {
    const text = draft;
    if (!text || completingRef.current) return;
    completingRef.current = true;
    setAutoCompleteAt(null);
    try {
      await clearBackendDraft();
      const message = { id: crypto.randomUUID(), role: "signer", text, createdAt: Date.now() };
      setMessages((current) => [...current, message]);
      await speak(text);
    } finally {
      completingRef.current = false;
    }
  }, [clearBackendDraft, draft, speak]);

  useEffect(() => {
    if (!autoCompleteAt) return undefined;
    const remaining = Math.max(0, autoCompleteAt - Date.now());
    const timer = window.setTimeout(completeDraft, remaining);
    return () => window.clearTimeout(timer);
  }, [autoCompleteAt, completeDraft]);

  const handleSpeechResult = useCallback((text) => {
    const cleanText = text.trim();
    if (!cleanText) return;
    const message = { id: crypto.randomUUID(), role: "speaker", text: cleanText, createdAt: Date.now() };
    setMessages((current) => [...current, message]);
    setSignPlayback(message);
  }, []);

  const handleBackspace = useCallback(async () => {
    const response = await fetch(`${API}/backspace`, { method: "POST" });
    if (!response.ok) throw new Error("Could not delete the last character");
    const data = await response.json();
    setPrediction((previous) => ({ ...(previous || {}), current_sentence: data.sentence }));
  }, []);

  return (
    <div className="app-shell">
      <Navbar connection={connection} />
      <main className="conversation-layout">
        <section className="camera-column">
          <CameraFeed onPrediction={handlePrediction} onConnectionChange={setConnection} />
          <div className="translation-overlay" aria-live="polite">
            <span>Live gesture draft</span>
            <strong>{draft || "Show one hand to begin"}</strong>
            <small>
              {prediction?.hand_present
                ? `${prediction?.pred_letter || "Checking gesture"} · ${prediction?.confidence || 0}% confidence`
                : draft
                  ? "Hand lowered — message completes after 5 seconds"
                  : "No hand detected — predictions paused"}
            </small>
          </div>
        </section>

        <aside className="conversation-panel">
          <ChatPanel
            messages={messages}
            draft={draft}
            prediction={prediction}
            autoCompleteAt={autoCompleteAt}
            onSpeak={speak}
          />

          {signPlayback && (
            <div className="speech-reference">
              <div className="speech-reference-heading">
                <div><span>Speech → sign playback</span><strong>{signPlayback.text}</strong></div>
                <button onClick={() => setSignPlayback(null)} aria-label="Close sign playback">×</button>
              </div>
              <SignDisplay key={signPlayback.id} sentence={signPlayback.text} autoPlay interval={1000} compact />
            </div>
          )}

          <div className="conversation-controls">
            <Controls
              draft={draft}
              onComplete={completeDraft}
              onSpeechResult={handleSpeechResult}
              onClear={clearBackendDraft}
              onBackspace={handleBackspace}
            />
          </div>
        </aside>
      </main>
    </div>
  );
}
