import { useEffect, useState } from "react";

export default function SignDisplay({ sentence = "", autoPlay = true, interval = 1000, compact = false }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [failedImage, setFailedImage] = useState(null);
  const [paused, setPaused] = useState(!autoPlay);
  const [speed, setSpeed] = useState(1);
  const words = sentence
    .toUpperCase()
    .trim()
    .split(/\s+/)
    .map((word) => [...word].filter((character) => /[A-Z0-9]/.test(character)))
    .filter((word) => word.length > 0);
  const letters = words.flat();
  const total = letters.length;
  const safeIndex = total ? currentIndex % total : 0;

  let traversed = 0;
  let currentWordIndex = 0;
  let currentIndexInWord = 0;
  for (let index = 0; index < words.length; index += 1) {
    if (safeIndex < traversed + words[index].length) {
      currentWordIndex = index;
      currentIndexInWord = safeIndex - traversed;
      break;
    }
    traversed += words[index].length;
  }
  const currentWord = words[currentWordIndex] || [];

  useEffect(() => {
    if (!autoPlay || paused || total < 2) return undefined;
    const timer = window.setInterval(
      () => setCurrentIndex((previous) => (previous + 1) % total),
      interval / speed,
    );
    return () => window.clearInterval(timer);
  }, [autoPlay, paused, total, interval, speed]);

  const currentLetter = letters[safeIndex] ?? null;
  const imageName = currentLetter?.toUpperCase();

  return (
    <section className={`sign-player ${compact ? "sign-player-compact" : ""}`}>
      <header><p>Sign playback</p>{total > 0 && <span>{safeIndex + 1} / {total}</span>}</header>
      <div className="sign-stage">
        {currentLetter ? <>
          {failedImage !== imageName ? (
            <img
              src={`/sign_images/${imageName}.png`}
              alt={`Sign for ${currentLetter}`}
              onError={() => setFailedImage(imageName)}
            />
          ) : (
            <div className="sign-placeholder"><span aria-hidden="true">🤟</span><p>Reference image unavailable</p></div>
          )}
          <strong>{currentLetter}</strong>
        </> : <div className="sign-placeholder"><span aria-hidden="true">🤟</span><p>Speak to start sign playback</p></div>}
      </div>
      {total > 0 && (
        <div className="sign-player-details">
          <p className="sign-word-label">Word {currentWordIndex + 1} of {words.length}</p>
          <div className="sign-sequence" aria-label={`Current word ${currentWord.join("")}`}>
            {currentWord.map((letter, index) => (
              <button
                key={`${letter}-${index}`}
                onClick={() => setCurrentIndex(traversed + index)}
                aria-label={`Show sign for ${letter}`}
                className={index === currentIndexInWord ? "active" : ""}
              >{letter}</button>
            ))}
          </div>
          <div className="sign-progress" aria-label={`${safeIndex + 1} of ${total}`}>
            <i style={{ width: `${((safeIndex + 1) / total) * 100}%` }} />
          </div>
          <div className="sign-navigation">
            <button onClick={() => setCurrentIndex((previous) => (previous - 1 + total) % total)}>← Previous</button>
            <button className="play-toggle" onClick={() => setPaused((value) => !value)}>{paused ? "▶ Play" : "Ⅱ Pause"}</button>
            <button onClick={() => setCurrentIndex((previous) => (previous + 1) % total)}>Next →</button>
          </div>
          <div className="sign-player-options">
            <button onClick={() => { setCurrentIndex(0); setPaused(false); }}>↻ Replay</button>
            <label>Speed
              <select value={speed} onChange={(event) => setSpeed(Number(event.target.value))}>
                <option value={0.75}>0.75×</option>
                <option value={1}>1×</option>
                <option value={1.5}>1.5×</option>
              </select>
            </label>
          </div>
        </div>
      )}
    </section>
  );
}
