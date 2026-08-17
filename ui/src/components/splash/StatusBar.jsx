import { motion } from "framer-motion";
import { FaCircle } from "react-icons/fa";

const statuses = [
  {
    title: "AI Engine",
    status: "ONLINE",
    color: "text-emerald-400",
  },
  {
    title: "Gesture Model",
    status: "LOADED",
    color: "text-cyan-400",
  },
  {
    title: "Camera",
    status: "CONNECTING",
    color: "text-yellow-400",
  },
];

export default function StatusBar() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 1 }}
      className="w-[420px] rounded-2xl bg-white/5 border border-white/10 backdrop-blur-xl p-5 shadow-xl"
    >
      {statuses.map((item, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{
            delay: index * 0.4,
            duration: 0.5,
          }}
          className="flex items-center justify-between py-2"
        >
          <div className="flex items-center gap-3">
            <FaCircle className={`${item.color} text-xs animate-pulse`} />
            <span className="text-slate-200">{item.title}</span>
          </div>

          <span className={`text-xs font-semibold ${item.color}`}>
            {item.status}
          </span>
        </motion.div>
      ))}
    </motion.div>
  );
}