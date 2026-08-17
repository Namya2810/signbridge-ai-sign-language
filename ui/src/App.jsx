import { Routes, Route, useNavigate } from "react-router-dom";
import { useEffect } from "react";

import SplashScreen from "./components/SplashScreen";
import Dashboard from "./pages/Dashboard";

function SplashWrapper() {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate("/dashboard");
    }, 3000);
    return () => clearTimeout(timer);
  }, []);

  return <SplashScreen onFinish={() => navigate("/dashboard")} />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/"          element={<SplashWrapper />} />
      <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
  );
}
