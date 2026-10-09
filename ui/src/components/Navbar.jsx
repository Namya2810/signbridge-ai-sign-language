import { FaHands } from "react-icons/fa6";

export default function Navbar({ connection = "connecting" }) {
  const label = {
    online: "AI ready",
    connecting: "Connecting",
    offline: "Offline",
    error: "Needs attention",
  }[connection];

  return (
    <header className="topbar">
      <div className="brand-lockup">
        <span className="brand-mark"><FaHands /></span>
        <div>
          <h1>SignBridge</h1>
          <p>Bi-directional communication prototype</p>
        </div>
      </div>
      <div className={`connection-pill connection-${connection}`}>
        <span />
        {label}
      </div>
    </header>
  );
}
