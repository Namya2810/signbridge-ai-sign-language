import { useEffect, useState } from "react";

import AnimatedBackground from "./splash/AnimatedBackground";
import FloatingHands from "./splash/FloatingHands";
import LogoAnimation from "./splash/LogoAnimation";
import LoadingPanel from "./splash/LoadingPanel";
import StatusBar from "./splash/StatusBar";

export default function SplashScreen({ onFinish }) {
  const loadingMessages = [
    "Booting Gesturio Core...",
    "Loading AI Neural Engine...",
    "Initializing Gesture Models...",
    "Calibrating Camera Input...",
    "Establishing Secure Session..."
  ];

  const [messageIndex, setMessageIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const splashDuration = setTimeout(() => {
      setExiting(true);

      // small delay before switching page
      setTimeout(() => {
        onFinish();
      }, 800);

    }, 6000);

    const messageTimer = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % loadingMessages.length);
    }, 1200);

    const progressTimer = setInterval(() => {
      setProgress((prev) => (prev >= 100 ? 100 : prev + 2));
    }, 100);

    return () => {
      clearTimeout(splashDuration);
      clearInterval(messageTimer);
      clearInterval(progressTimer);
    };
  }, [onFinish]);

  return (
    <div className={`relative min-h-screen overflow-hidden flex items-center justify-center transition-all duration-700
      ${exiting ? "opacity-0 scale-105 blur-sm" : "opacity-100 scale-100"}`}>

      {/* Background */}
      <AnimatedBackground />
      <FloatingHands />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center">

        <LogoAnimation />

        <h1 className="mt-10 text-6xl font-black tracking-[10px] text-white">
          GESTURIO
        </h1>

        <p className="text-muted mt-3 text-sm">
          AI Gesture Recognition System
        </p>

        {/* Status */}
        <div className="mt-6 glass px-4 py-2 rounded-full text-sm text-muted border border-white/10">
          System Boot Sequence Active
        </div>

        {/* Loading */}
        <div className="mt-10 w-[320px]">
          <LoadingPanel message={loadingMessages[messageIndex]} />

          <div className="mt-4 h-2 w-full bg-white/5 rounded-full overflow-hidden border border-white/10">
            <div
              className="h-full bg-gradient-to-r from-emerald-400 to-blue-500 transition-all duration-200"
              style={{ width: `${progress}%` }}
            />
          </div>

          <p className="text-center text-muted text-xs mt-2">
            Initializing... {progress}%
          </p>
        </div>

        <div className="mt-10">
          <StatusBar />
        </div>

      </div>
    </div>
  );
}