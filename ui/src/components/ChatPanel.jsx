import { useEffect, useRef } from "react";

/**
 * ChatPanel — real-time predictions + sentence display.
 * prediction prop: { hand_present, pred_letter, confidence,
 *                   current_sentence, progress }
 */
export default function ChatPanel({ prediction }) {
  const scrollRef = useRef(null);

  // Auto-scroll jab naya letter aaye
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [prediction?.current_sentence]);

  const sentence   = prediction?.current_sentence ?? "";
  const letter     = prediction?.pred_letter ?? "";
  const confidence = prediction?.confidence ?? 0;
  const progress   = prediction?.progress ?? 0;
  const handPresent = prediction?.hand_present ?? false;

  // Sentence ko words mein split karo display ke liye
  const words = sentence.trim().split(/\s+/).filter(Boolean);

  return (
    <div className="glass rounded-2xl p-5 h-[550px] border border-white/10 flex flex-col">

      {/* Header */}
      <h2 className="text-white text-lg font-semibold">Recognition Stream</h2>
      <p className="text-muted text-sm mt-1 mb-3">Live AI gesture detection</p>

      {/* Current letter + confidence */}
      <div className="mb-3">
        {handPresent && letter ? (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-4xl font-bold text-emerald-400">{letter}</span>
              <div className="flex flex-col">
                <span className="text-xs text-muted">Detecting</span>
                <span className="text-sm text-white font-medium">{confidence}%</span>
              </div>
            </div>

            {/* Stability progress bar */}
            <div className="flex flex-col items-end gap-1">
              <span className="text-xs text-muted">Stability</span>
              <div className="w-20 h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-400 rounded-full transition-all duration-100"
                  style={{ width: `${progress * 100}%` }}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3">
            <p className="text-muted text-sm animate-pulse">
              {handPresent ? "Low confidence..." : "Waiting for gesture..."}
            </p>
          </div>
        )}
      </div>

      {/* Current sentence */}
      <div className="mb-3">
        <p className="text-xs text-muted mb-1">Current Sentence</p>
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl px-4 py-3 min-h-[52px]">
          {sentence ? (
            <p className="text-white font-medium text-lg tracking-wide break-all">
              {sentence}
              <span className="animate-pulse text-emerald-400 ml-0.5">|</span>
            </p>
          ) : (
            <p className="text-slate-600 text-sm">Start signing...</p>
          )}
        </div>
      </div>

      {/* Word history */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1" ref={scrollRef}>
        <p className="text-xs text-muted mb-2">Detected Words</p>

        {words.length === 0 && (
          <div className="flex items-center justify-center h-24">
            <p className="text-muted text-sm animate-pulse">No words yet...</p>
          </div>
        )}

        {[...words].reverse().map((word, index) => (
          <div
            key={index}
            className="bg-slate-800 rounded-xl px-4 py-3 border border-slate-700 shadow-md"
          >
            <span className="text-white font-medium">{word}</span>
            <span className="text-xs text-emerald-400 ml-2">detected</span>
          </div>
        ))}
      </div>
    </div>
  );
}
