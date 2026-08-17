import { motion } from "framer-motion";
import { FaRegHandPaper } from "react-icons/fa";

export default function LogoAnimation() {
  return (
    <div className="relative flex items-center justify-center w-72 h-72">

      {/* Background Glow */}
      <motion.div
        animate={{
          scale: [1, 1.15, 1],
          opacity: [0.25, 0.45, 0.25],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
        }}
        className="absolute w-64 h-64 rounded-full bg-emerald-400 blur-[90px]"
      />

      {/* Outer Ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute w-72 h-72 rounded-full border border-cyan-400/20"
      />

      {/* Middle Ring */}
      <motion.div
        animate={{ rotate: -360 }}
        transition={{
          duration: 16,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute w-60 h-60 rounded-full border-2 border-dashed border-emerald-400/20"
      />

      {/* Orbiting Dot */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "linear",
        }}
        className="absolute w-60 h-60"
      >
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-cyan-400 shadow-[0_0_20px_#22d3ee]" />
      </motion.div>

      {/* Glass Orb */}
      <motion.div
        initial={{
          scale: 0,
          rotate: -90,
          opacity: 0,
        }}
        animate={{
          scale: 1,
          rotate: 0,
          opacity: 1,
        }}
        transition={{
          duration: 1.2,
        }}
        className="relative w-40 h-40 rounded-full bg-white/10 backdrop-blur-2xl border border-white/10 shadow-[0_0_60px_rgba(16,185,129,.45)] flex items-center justify-center overflow-hidden"
      >

        {/* Shine Effect */}
        <motion.div
          animate={{
            x: [-200, 200],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "linear",
          }}
          className="absolute w-16 h-56 rotate-12 bg-white/20 blur-xl"
        />

        {/* Floating Hand */}
        <motion.div
          animate={{
            y: [0, -8, 0],
            rotate: [-3, 3, -3],
            scale: [1, 1.05, 1],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
          }}
        >
          <FaRegHandPaper className="text-7xl text-emerald-300 drop-shadow-[0_0_25px_rgba(16,185,129,.8)]" />
        </motion.div>

      </motion.div>

    </div>
  );
}