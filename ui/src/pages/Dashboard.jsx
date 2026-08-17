import { useState } from "react";
import Navbar      from "../components/Navbar";
import CameraFeed  from "../components/CameraFeed";
import ChatPanel   from "../components/ChatPanel";
import Controls    from "../components/Controls";
import SignDisplay  from "../components/SignDisplay";
import Footer      from "../components/footer";

export default function Dashboard() {
  const [prediction,  setPrediction]  = useState(null);
  const [sttResult,   setSttResult]   = useState("");

  const handleSentenceChange = (newSentence) => {
    setPrediction((prev) =>
      prev ? { ...prev, current_sentence: newSentence } : prev
    );
  };

  const sentence = prediction?.current_sentence ?? "";

  // SignDisplay shows: STT result if available, else signed sentence
  const displayText = sttResult || sentence;

  return (
    <div className="min-h-screen bg-slate-900 animate-fade-in">
      <Navbar />

      <div className="p-6 space-y-6">

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* LEFT — Camera (takes 2 cols) */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            <CameraFeed onPrediction={setPrediction} />

            {/* Stats bar below camera — fills the black space */}
            <div className="grid grid-cols-3 gap-4">
              <div className="glass rounded-xl p-4 border border-white/10 text-center">
                <p className="text-xs text-muted mb-1">Current Letter</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {prediction?.pred_letter || "—"}
                </p>
              </div>
              <div className="glass rounded-xl p-4 border border-white/10 text-center">
                <p className="text-xs text-muted mb-1">Confidence</p>
                <p className="text-2xl font-bold text-blue-400">
                  {prediction?.confidence ? `${prediction.confidence}%` : "—"}
                </p>
              </div>
              <div className="glass rounded-xl p-4 border border-white/10 text-center">
                <p className="text-xs text-muted mb-1">Letters Signed</p>
                <p className="text-2xl font-bold text-purple-400">
                  {sentence.replace(/ /g, "").length || 0}
                </p>
              </div>
            </div>
          </div>

          {/* RIGHT column */}
          <div className="flex flex-col gap-4">

            {/* Chat Panel */}
            <ChatPanel prediction={prediction} />

            {/* Sign Reference Slideshow */}
            <SignDisplay
              sentence={displayText}
              autoPlay={true}
              interval={1200}
            />

          </div>
        </div>

        {/* Controls */}
        <div className="glass p-6">
          <Controls
            sentence={sentence}
            onSentenceChange={handleSentenceChange}
            onSttResult={setSttResult}
          />
        </div>

        <Footer />
      </div>
    </div>
  );
}
