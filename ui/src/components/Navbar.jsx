export default function Navbar() {
  return (
    <nav className="flex justify-between items-center px-8 py-4 border-b border-white/10 bg-[#0b1220]">

      {/* LEFT: Brand */}
      <div className="flex flex-col">

        <h1 className="text-xl font-bold text-gradient tracking-wide">
          Gesturio
        </h1>

        <p className="text-muted text-xs mt-1">
          Every Gesture Has a Voice
        </p>

      </div>

      {/* CENTER: SYSTEM STATUS (NEW) */}
      <div className="hidden md:flex items-center gap-3 glass px-4 py-2 rounded-full border border-white/10">

        {/* Pulse dot */}
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-soft-pulse"></span>

        <span className="text-sm text-muted">
          AI System Active
        </span>

        <span className="text-xs text-emerald-400">
          v2.1 Neural Engine
        </span>

      </div>

      {/* RIGHT: USER / STATUS */}
      <div className="flex items-center gap-3">

        {/* Online badge */}
        <div className="glass px-3 py-1 rounded-full flex items-center gap-2 border border-white/10">

          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>

          <span className="text-sm text-muted">
            Online
          </span>

        </div>

      </div>

    </nav>
  );
}