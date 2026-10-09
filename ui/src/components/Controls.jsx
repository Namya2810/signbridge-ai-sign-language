import { useEffect, useState } from "react";
import { FaBackspace, FaCheck, FaMicrophone, FaTrash } from "react-icons/fa";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function Controls({ draft, onComplete, onSpeechResult, onClear, onBackspace }) {
  const [sttStatus, setSttStatus] = useState("idle");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!["starting", "recording", "processing"].includes(sttStatus)) return undefined;
    const poll = window.setInterval(async () => {
      try {
        const response = await fetch(`${API}/stt/result`);
        if (!response.ok) throw new Error();
        const data = await response.json();
        setSttStatus(data.status);
        if (data.status === "done") {
          onSpeechResult?.(data.result || "");
          window.clearInterval(poll);
        } else if (data.status === "error") {
          setError(data.error || "Speech recognition failed.");
          window.clearInterval(poll);
        }
      } catch {
        setError("Cannot reach the speech service.");
        setSttStatus("error");
        window.clearInterval(poll);
      }
    }, 700);
    return () => window.clearInterval(poll);
  }, [sttStatus, onSpeechResult]);

  const listen = async () => {
    setError("");
    try {
      const response = await fetch(`${API}/stt/start`, { method: "POST" });
      if (!response.ok) throw new Error();
      setSttStatus("starting");
    } catch {
      setError("Microphone recording could not start.");
      setSttStatus("error");
    }
  };

  const run = async (action, failureMessage) => {
    setError("");
    try { await action(); } catch { setError(failureMessage); }
  };

  const listening = ["starting", "recording", "processing"].includes(sttStatus);
  const micLabel = { idle: "Speak", starting: "Starting…", recording: "Listening…", processing: "Transcribing…", done: "Speak again", error: "Try microphone" }[sttStatus];

  return (
    <div className="control-stack">
      {error && <p className="control-error" role="alert">{error}</p>}
      <button className="complete-button" onClick={() => run(onComplete, "Could not complete this message.")} disabled={!draft}>
        <FaCheck /><span><strong>Complete & Speak</strong><small>Add the signed text to chat and read it aloud</small></span>
      </button>
      <div className="secondary-controls">
        <button className={listening ? "mic-active" : ""} onClick={listen} disabled={listening}><FaMicrophone /><span>{micLabel}</span></button>
        <button onClick={() => run(onBackspace, "Could not delete the last character.")} disabled={!draft}><FaBackspace /><span>Delete</span></button>
        <button onClick={() => run(onClear, "Could not clear the live draft.")} disabled={!draft}><FaTrash /><span>Clear</span></button>
      </div>
      <p className="control-hint">Lower your hand for 5 seconds to complete automatically.</p>
    </div>
  );
}
