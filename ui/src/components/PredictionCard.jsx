export default function PredictionCard({ prediction, confidence }) {
  return (
    <div className="glass mt-6 rounded-2xl p-6 border border-white/10">

      <p className="text-muted uppercase tracking-widest text-xs">
        Detected Sign
      </p>

      <h1 className="text-white text-4xl font-bold mt-3">
        {prediction}
      </h1>

      <p className="text-emerald-400 mt-3 text-sm">
        Confidence: {confidence}%
      </p>

    </div>
  );
}