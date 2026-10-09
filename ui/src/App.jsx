import { useEffect, useState } from "react";
import SplashScreen from "./components/SplashScreen";
import Dashboard from "./pages/Dashboard";

export default function App() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setReady(true), 1600);
    return () => window.clearTimeout(timer);
  }, []);

  return ready ? <Dashboard /> : <SplashScreen onFinish={() => setReady(true)} />;
}
