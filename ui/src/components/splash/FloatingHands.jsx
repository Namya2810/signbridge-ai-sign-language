import { motion } from "framer-motion";
import {
  FaRegHandPaper,
  FaHandPeace,
  FaRegHandshake,
  FaHandPointUp,
  FaHandSpock,
} from "react-icons/fa";

const hands = [
  {
    icon: <FaRegHandPaper />,
    top: "15%",
    left: "10%",
    size: "text-5xl",
    delay: 0,
  },
  {
    icon: <FaHandPeace />,
    top: "20%",
    right: "12%",
    size: "text-4xl",
    delay: 1,
  },
  {
    icon: <FaHandPointUp />,
    bottom: "18%",
    left: "15%",
    size: "text-4xl",
    delay: 2,
  },
  {
    icon: <FaRegHandshake />,
    bottom: "15%",
    right: "15%",
    size: "text-5xl",
    delay: 3,
  },
  {
    icon: <FaHandSpock />,
    top: "45%",
    right: "5%",
    size: "text-6xl",
    delay: 1.5,
  },
];

export default function FloatingHands() {
  return (
    <>
      {hands.map((hand, index) => (
        <motion.div
          key={index}
          className={`absolute text-emerald-400/25 ${hand.size} drop-shadow-[0_0_25px_rgba(16,185,129,0.5)]`}
          style={{
            top: hand.top,
            left: hand.left,
            right: hand.right,
            bottom: hand.bottom,
          }}
          animate={{
            y: [0, -25, 0],
            rotate: [-8, 8, -8],
            opacity: [0.2, 0.5, 0.2],
            scale: [1, 1.08, 1],
          }}
          transition={{
            duration: 5,
            repeat: Infinity,
            delay: hand.delay,
            ease: "easeInOut",
          }}
        >
          {hand.icon}
        </motion.div>
      ))}
    </>
  );
}