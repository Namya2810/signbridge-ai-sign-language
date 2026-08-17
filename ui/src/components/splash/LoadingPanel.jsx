import { motion } from "framer-motion";
import { FaRegHandPaper } from "react-icons/fa";

export default function LogoAnimation() {
  return (
    <div className="relative flex items-center justify-center">

      {/* Outer Ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{
          duration: 18,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute w-64 h-64 rounded-full border border-emerald-400/20"
      />

      {/* Middle Ring */}
      <motion.div
        animate={{ rotate: -360 }}
        transition={{
          duration: 12,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute w-52 h-52 rounded-full border border-cyan-400/20 border-dashed"
      />

      {/* Pulse */}
      <motion.div
        animate={{
          scale: [1, 1.15, 1],
          opacity: [0.4, 0.8, 0.4],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
        }}
        className="absolute w-44 h-44 rounded-full bg-emerald-500/20 blur-3xl"
      />

      {/* Glass Orb */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{
          scale: 1,
          opacity: 1,
        }}
        transition={{
          duration: 1,
        }}
        className="relative w-40 h-40 rounded-full bg-white/10 backdrop-blur-2xl border border-white/10 shadow-[0_0_60px_rgba(16,185,129,0.45)] flex items-center justify-center"
      >
        <motion.div
          animate={{
            y: [0, -8, 0],
          }}
          transition={{
            duration: 2.5,
            repeat: Infinity,
          }}
        >
          <FaRegHandPaper className="text-7xl text-emerald-300" />
        </motion.div>
      </motion.div>
    </div>
  );
}