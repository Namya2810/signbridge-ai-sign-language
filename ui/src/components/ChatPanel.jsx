import { useEffect, useRef, useState } from "react";
import { FaVolumeUp } from "react-icons/fa";

export default function ChatPanel({ messages, draft, prediction, autoCompleteAt, onSpeak }) {
  const listRef = useRef(null);
  const [clock, setClock] = useState(0);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, draft]);

  useEffect(() => {
    if (!autoCompleteAt) return undefined;
    const timer = window.setInterval(() => setClock(Date.now()), 250);
    return () => window.clearInterval(timer);
  }, [autoCompleteAt]);

  const secondsLeft = autoCompleteAt ? (clock ? Math.max(0, Math.ceil((autoCompleteAt - clock) / 1000)) : 5) : null;

  return (
    <section className="chat-card">
      <header className="chat-header">
        <div><h2>Conversation</h2><p>Gesture and voice messages appear here</p></div>
        <span className="live-dot">Live</span>
      </header>

      <div className="chat-messages" ref={listRef} aria-live="polite">
        {messages.length === 0 && !draft && (
          <div className="chat-empty"><span>🤟</span><strong>Start a conversation</strong><p>Sign in the camera or tap the microphone.</p></div>
        )}
        {messages.map((message) => (
          <article key={message.id} className={`message-row message-${message.role}`}>
            <div className="message-label">{message.role === "signer" ? "Signed message" : "Spoken message"}</div>
            <div className="message-bubble">
              <p>{message.text}</p>
              {message.role === "signer" && <button onClick={() => onSpeak(message.text)} aria-label={`Speak ${message.text}`}><FaVolumeUp /></button>}
            </div>
          </article>
        ))}
        {draft && (
          <article className="message-row message-draft">
            <div className="message-label">Detecting now</div>
            <div className="message-bubble draft-bubble">
              <p>{draft}<span className="typing-cursor">|</span></p>
              <span>{secondsLeft !== null ? `Completing in ${secondsLeft}s` : "Hold each gesture steady"}</span>
            </div>
          </article>
        )}
      </div>

      <div className="detector-strip">
        <div className="detected-letter">{prediction?.pred_letter || "—"}</div>
        <div>
          <strong>
            {prediction?.pred_letter
              ? "Gesture recognized"
              : prediction?.hand_present
                ? "Hold or adjust gesture"
                : "Waiting for a clear hand"}
          </strong>
          <span>{prediction?.confidence || 0}% model confidence</span>
        </div>
        <div className="stability-track"><i style={{ width: `${(prediction?.progress || 0) * 100}%` }} /></div>
      </div>
    </section>
  );
}
