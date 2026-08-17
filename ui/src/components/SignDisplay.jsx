import { useState, useEffect } from "react";

/**
 * SignDisplay — current sentence ke letters ka slideshow.
 * Har letter ki sign image dikhata hai ek ek karke.
 * Images: /sign_images/A.png, B.png ... 0.png, 1.png etc.
 *
 * Props:
 *   sentence  — string, e.g. "HELLO"
 *   autoPlay  — bool, auto-advance karo (default true)
 *   interval  — ms per letter (default 1000)
 */
export default function SignDisplay({ sentence = "", autoPlay = true, interval = 1000 }) {
  const [currentIndex, setCurrentIndex] = useState(0);

  // Sentence se letters nikalo (spaces skip karo)
  const letters = sentence
    .toUpperCase()
    .split("")
    .filter((ch) => ch !== " " && ch.match(/[A-Z0-9]/));

  const total = letters.length;

  // Reset when sentence changes
  useEffect(() => {
    setCurrentIndex(0);
  }, [sentence]);

  // Auto-play slideshow
  useEffect(() => {
    if (!autoPlay || total === 0) return;

    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % total);
    }, interval);

    return () => clearInterval(timer);
  }, [autoPlay, total, interval]);

  const currentLetter = letters[currentIndex] ?? null;
  const imgSrc = currentLetter ? `/sign_images/${currentLetter}.png` : null;

  return (
    <div className="glass rounded-2xl border border-white/10 p-4 flex flex-col items-center gap-3">

      {/* Header */}
      <div className="w-full flex items-center justify-between">
        <p className="text-xs text-muted">Sign Reference</p>
        {total > 0 && (
          <p className="text-xs text-emerald-400">
            {currentIndex + 1} / {total}
          </p>
        )}
      </div>

      {/* Image display */}
      <div className="w-full aspect-square bg-slate-800/60 rounded-xl overflow-hidden flex items-center justify-center border border-slate-700/50 relative">
        {imgSrc ? (
          <>
            <img
              key={currentLetter}
              src={imgSrc}
              alt={`Sign for ${currentLetter}`}
              className="w-full h-full object-contain p-2 animate-fade-in"
              onError={(e) => {
                e.target.style.display = "none";
              }}
            />
            {/* Letter overlay */}
            <div className="absolute bottom-2 right-2 bg-black/60 rounded-lg px-2 py-1">
              <span className="text-emerald-400 font-bold text-lg">
                {currentLetter}
              </span>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <span className="text-4xl">🤟</span>
            <p className="text-muted text-xs text-center">
              {sentence ? "Loading..." : "Sign something\nto see reference"}
            </p>
          </div>
        )}
      </div>

      {/* Letter strip — all letters in sentence */}
      {total > 0 && (
        <div className="w-full flex flex-wrap gap-1 justify-center">
          {letters.map((letter, i) => (
            <button
              key={i}
              onClick={() => setCurrentIndex(i)}
              className={`w-7 h-7 rounded-md text-xs font-bold transition-all
                ${i === currentIndex
                  ? "bg-emerald-500 text-white scale-110"
                  : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                }`}
            >
              {letter}
            </button>
          ))}
        </div>
      )}

      {/* Manual controls */}
      {total > 1 && (
        <div className="flex gap-3">
          <button
            onClick={() => setCurrentIndex((prev) => (prev - 1 + total) % total)}
            className="text-xs px-3 py-1 rounded-lg bg-slate-700 hover:bg-slate-600 text-white transition"
          >
            ← Prev
          </button>
          <button
            onClick={() => setCurrentIndex((prev) => (prev + 1) % total)}
            className="text-xs px-3 py-1 rounded-lg bg-slate-700 hover:bg-slate-600 text-white transition"
          >
            Next →
          </button>
        </div>
      )}

    </div>
  );
}
