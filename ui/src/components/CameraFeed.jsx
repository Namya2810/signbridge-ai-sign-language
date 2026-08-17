import { useEffect, useRef, useCallback } from "react";
import Webcam from "react-webcam";
import { FaVideo, FaExpand } from "react-icons/fa";

/**
 * CameraFeed — webcam frames ko backend WebSocket pe bhejta hai.
 * onPrediction(result) callback se parent ko data milta hai.
 */
export default function CameraFeed({ onPrediction }) {
  const webcamRef = useRef(null);
  const wsRef     = useRef(null);
  const timerRef  = useRef(null);

  // ── WebSocket connect ──────────────────────────────────────────────────
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket("ws://localhost:8000/ws/predict");

      ws.onopen = () => {
        console.log("WS connected");
        wsRef.current = ws;
        startSending();
      };

      ws.onmessage = (e) => {
        const result = JSON.parse(e.data);
        if (onPrediction) onPrediction(result);
      };

      ws.onclose = () => {
        console.log("WS closed, reconnecting in 2s...");
        clearInterval(timerRef.current);
        setTimeout(connect, 2000);
      };

      ws.onerror = (err) => {
        console.error("WS error", err);
        ws.close();
      };
    };

    connect();

    return () => {
      clearInterval(timerRef.current);
      wsRef.current?.close();
    };
  }, []);

  // ── Frame sender — har 100ms (10 fps to backend) ──────────────────────
  const startSending = useCallback(() => {
    timerRef.current = setInterval(() => {
      if (
        webcamRef.current &&
        wsRef.current?.readyState === WebSocket.OPEN
      ) {
        const imageSrc = webcamRef.current.getScreenshot();
        if (imageSrc) {
          wsRef.current.send(imageSrc);
        }
      }
    }, 100);
  }, []);

  return (
    <div className="relative glass rounded-2xl overflow-hidden h-[550px] border border-white/10 animate-float-soft animate-glow">

      {/* TOP HUD BAR */}
      <div className="absolute top-0 left-0 w-full z-10 flex items-center justify-between px-4 py-3 bg-black/20 backdrop-blur-md">
        <div className="flex items-center gap-2 text-emerald-400 text-sm">
          <FaVideo />
          <span>AI Vision System</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted">
          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-soft-pulse"></span>
          ACTIVE
        </div>
      </div>

      {/* Webcam */}
      <Webcam
        ref={webcamRef}
        audio={false}
        screenshotFormat="image/jpeg"
        screenshotQuality={0.7}
        className="w-full h-full object-cover scale-[1.03]"
        mirrored={true}
      />

      {/* SCANNING GRID OVERLAY */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.2) 1px, transparent 1px)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="absolute w-full h-1 bg-gradient-to-r from-transparent via-emerald-400 to-transparent opacity-70 animate-pulse top-1/2" />
      </div>

      {/* CORNER FRAME GLOW */}
      <div className="absolute inset-0 pointer-events-none shadow-[inset_0_0_80px_rgba(34,197,94,0.18)]" />

      {/* BOTTOM STATUS BAR */}
      <div className="absolute bottom-0 left-0 w-full px-4 py-3 bg-black/20 backdrop-blur-md flex justify-between text-xs text-muted">
        <span>Gesture Tracking: ON</span>
        <span className="text-emerald-400">Neural Model: v2.1</span>
      </div>

      {/* FULLSCREEN ICON */}
      <div className="absolute top-3 right-12 text-white/60 hover:text-white cursor-pointer">
        <FaExpand />
      </div>

    </div>
  );
}
