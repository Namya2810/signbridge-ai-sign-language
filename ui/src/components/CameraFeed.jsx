import { useCallback, useEffect, useRef, useState } from "react";
import Webcam from "react-webcam";
import { FaCamera, FaExpand } from "react-icons/fa";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const WS_URL = API_URL.replace(/^http/, "ws");

export default function CameraFeed({ onPrediction, onConnectionChange }) {
  const webcamRef = useRef(null);
  const containerRef = useRef(null);
  const wsRef = useRef(null);
  const sendTimerRef = useRef(null);
  const reconnectRef = useRef(null);
  const mountedRef = useRef(false);
  const predictionRef = useRef(onPrediction);
  const connectionRef = useRef(onConnectionChange);
  const [status, setStatus] = useState("connecting");
  const [message, setMessage] = useState("Starting camera and AI engine…");

  useEffect(() => {
    predictionRef.current = onPrediction;
    connectionRef.current = onConnectionChange;
  }, [onPrediction, onConnectionChange]);

  const updateStatus = useCallback((next, detail) => {
    setStatus(next);
    setMessage(detail);
    connectionRef.current?.(next);
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    const stopSending = () => {
      window.clearInterval(sendTimerRef.current);
      sendTimerRef.current = null;
    };

    const connect = () => {
      if (!mountedRef.current) return;
      updateStatus("connecting", "Connecting to recognition service…");
      const ws = new WebSocket(`${WS_URL}/ws/predict`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        updateStatus("online", "Live recognition ready");
        stopSending();
        sendTimerRef.current = window.setInterval(() => {
          if (ws.readyState !== WebSocket.OPEN || ws.bufferedAmount > 250_000) return;
          const image = webcamRef.current?.getScreenshot();
          if (image) ws.send(image);
        }, 140);
      };

      ws.onmessage = ({ data }) => {
        try {
          const result = JSON.parse(data);
          if (result.type === "error") {
            updateStatus("error", result.message || "Recognition service error");
            return;
          }
          predictionRef.current?.(result);
        } catch {
          updateStatus("error", "Received an invalid recognition response");
        }
      };

      ws.onerror = () => ws.close();
      ws.onclose = () => {
        stopSending();
        if (!mountedRef.current) return;
        updateStatus("offline", "Backend offline — retrying…");
        reconnectRef.current = window.setTimeout(connect, 2500);
      };
    };

    connect();
    return () => {
      mountedRef.current = false;
      stopSending();
      window.clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [updateStatus]);

  const enterFullscreen = () => containerRef.current?.requestFullscreen?.();
  const statusColor = {
    online: "bg-emerald-400",
    connecting: "bg-amber-400",
    offline: "bg-rose-400",
    error: "bg-rose-400",
  }[status];

  return (
    <section ref={containerRef} className="camera-shell" aria-label="Live sign recognition camera">
      <Webcam
        ref={webcamRef}
        audio={false}
        mirrored
        screenshotFormat="image/jpeg"
        screenshotQuality={0.78}
        videoConstraints={{ width: 960, height: 720, facingMode: "user" }}
        className="h-full w-full object-cover"
        onUserMediaError={() => updateStatus("error", "Camera permission is required")}
      />

      <div className="camera-topbar">
        <div className="flex items-center gap-2.5">
          <FaCamera className="text-emerald-300" aria-hidden="true" />
          <div>
            <p className="text-sm font-semibold text-white">Recognition camera</p>
            <p className="text-xs text-slate-300">Keep the complete hand sign inside the guide</p>
          </div>
        </div>
        <button className="icon-button" onClick={enterFullscreen} aria-label="Open camera fullscreen">
          <FaExpand />
        </button>
      </div>

      <div className="hand-guide" aria-hidden="true">
        <span className="guide-corner guide-tl" />
        <span className="guide-corner guide-tr" />
        <span className="guide-corner guide-bl" />
        <span className="guide-corner guide-br" />
      </div>

      <div className="camera-status" role="status">
        <span className={`h-2 w-2 rounded-full ${statusColor} ${status === "online" ? "animate-pulse" : ""}`} />
        <span>{message}</span>
      </div>
    </section>
  );
}
