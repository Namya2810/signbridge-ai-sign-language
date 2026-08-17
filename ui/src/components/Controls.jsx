import { useState, useEffect } from "react";
import { FaMicrophone, FaVolumeUp, FaTrash, FaBackspace } from "react-icons/fa";

const API = "http://localhost:8000";

export default function Controls({ sentence = "", onSentenceChange, onSttResult }) {

  const [sttStatus,  setSttStatus]  = useState("idle");
  const [sttResult,  setSttResult]  = useState("");
  const [ttsBusy,    setTtsBusy]    = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);

  // Poll STT result
  useEffect(() => {
    if (sttStatus !== "recording" && sttStatus !== "processing") return;

    const poll = setInterval(async () => {
      try {
        const res  = await fetch(`${API}/stt/result`);
        const data = await res.json();
        setSttStatus(data.status);
        if (data.status === "done") {
          setSttResult(data.result);
          if (onSttResult) onSttResult(data.result);  // pass to Dashboard → SignDisplay
          clearInterval(poll);
        }
      } catch (e) {
        console.error("STT poll error", e);
      }
    }, 800);

    return () => clearInterval(poll);
  }, [sttStatus]);

  const handleListen = async () => {
    if (sttStatus === "recording" || sttStatus === "processing") return;
    setSttResult("");
    if (onSttResult) onSttResult("");
    setSttStatus("idle");
    try {
      await fetch(`${API}/stt/start`, { method: "POST" });
      setSttStatus("recording");
    } catch (e) {
      console.error("STT start error", e);
    }
  };

  const handleTalk = async () => {
    if (!ttsEnabled || ttsBusy || !sentence.trim()) return;
    setTtsBusy(true);
    try {
      await fetch(`${API}/tts`, {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({ text: sentence.trim() }),
      });
    } catch (e) {
      console.error("TTS error", e);
    }
    setTimeout(() => setTtsBusy(false), 3000);
  };

  const handleClear = async () => {
    try {
      await fetch(`${API}/clear`, { method: "POST" });
      if (onSentenceChange) onSentenceChange("");
      setSttResult("");
      if (onSttResult) onSttResult("");
      setSttStatus("idle");
    } catch (e) {
      console.error("Clear error", e);
    }
  };

  const handleBackspace = async () => {
    try {
      const res  = await fetch(`${API}/backspace`, { method: "POST" });
      const data = await res.json();
      if (onSentenceChange) onSentenceChange(data.sentence);
    } catch (e) {
      console.error("Backspace error", e);
    }
  };

  const listenLabel = {
    idle       : "Listen",
    recording  : "Recording...",
    processing : "Processing...",
    done       : "Done ✓",
  }[sttStatus];

  const listenBorder = {
    idle       : "hover:border-emerald-400/40",
    recording  : "border-red-400/60 bg-red-400/10",
    processing : "border-yellow-400/60 bg-yellow-400/10",
    done       : "border-emerald-400/60 bg-emerald-400/10",
  }[sttStatus];

  return (
    <div className="flex flex-col items-center gap-4">

      {/* STT result */}
      {sttResult && (
        <div className="w-full max-w-2xl bg-slate-800/80 border border-blue-400/30 rounded-xl px-5 py-3">
          <p className="text-xs text-muted mb-1">Speech Detected:</p>
          <p className="text-white font-medium">{sttResult}</p>
        </div>
      )}

      {/* Buttons */}
      <div className="flex justify-center gap-4 flex-wrap">

        {/* Listen */}
        <button
          onClick={handleListen}
          disabled={sttStatus === "recording" || sttStatus === "processing"}
          className={`glass w-48 px-5 py-4 rounded-xl text-white border border-white/10 transition group
            ${listenBorder} disabled:opacity-60 disabled:cursor-not-allowed`}
        >
          <div className="flex flex-col items-start">
            <div className="flex items-center gap-3">
              <FaMicrophone className={`transition ${sttStatus === "recording" ? "text-red-400 animate-pulse" : "text-emerald-400"}`} />
              <span className="font-medium">{listenLabel}</span>
            </div>
            <span className="text-xs text-muted mt-2">Speech → Text (6s)</span>
          </div>
        </button>

        {/* Talk */}
        <button
          onClick={handleTalk}
          disabled={!ttsEnabled || ttsBusy || !sentence.trim()}
          className={`glass w-48 px-5 py-4 rounded-xl text-white border border-white/10 transition group
            hover:border-blue-400/40 ${ttsBusy ? "border-blue-400/60 bg-blue-400/10" : ""}
            disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <div className="flex flex-col items-start">
            <div className="flex items-center gap-3">
              <FaVolumeUp className={`text-blue-400 transition ${ttsBusy ? "animate-pulse" : ""}`} />
              <span className="font-medium">{ttsBusy ? "Speaking..." : "Talk"}</span>
            </div>
            <span className="text-xs text-muted mt-2">
              {sentence.trim() ? `"${sentence.slice(0, 18)}${sentence.length > 18 ? "…" : ""}"` : "Sign first"}
            </span>
          </div>
        </button>

        {/* Clear */}
        <button
          onClick={handleClear}
          className="glass w-36 px-5 py-4 rounded-xl text-white border border-white/10 hover:border-red-400/40 transition group"
        >
          <div className="flex flex-col items-start">
            <div className="flex items-center gap-3">
              <FaTrash className="text-red-400" />
              <span className="font-medium">Clear</span>
            </div>
            <span className="text-xs text-muted mt-2">Reset all</span>
          </div>
        </button>

        {/* Backspace */}
        <button
          onClick={handleBackspace}
          disabled={!sentence}
          className="glass w-36 px-5 py-4 rounded-xl text-white border border-white/10 hover:border-yellow-400/40 transition group disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <div className="flex flex-col items-start">
            <div className="flex items-center gap-3">
              <FaBackspace className="text-yellow-400" />
              <span className="font-medium">Delete</span>
            </div>
            <span className="text-xs text-muted mt-2">Last letter</span>
          </div>
        </button>

      </div>

      {/* TTS toggle */}
      <button
        onClick={() => setTtsEnabled(!ttsEnabled)}
        className={`text-xs px-4 py-1.5 rounded-full border transition
          ${ttsEnabled ? "border-emerald-400/40 text-emerald-400 bg-emerald-400/10"
                       : "border-slate-600 text-slate-500"}`}
      >
        TTS {ttsEnabled ? "ON" : "OFF"}
      </button>

    </div>
  );
}
