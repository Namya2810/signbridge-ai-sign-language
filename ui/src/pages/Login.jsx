import { Link, useNavigate } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b1220] relative overflow-hidden">

      {/* Glow Background */}
      <div className="absolute w-[500px] h-[500px] bg-emerald-500/10 blur-[120px] rounded-full top-[-120px] left-[-120px]" />
      <div className="absolute w-[500px] h-[500px] bg-blue-500/10 blur-[120px] rounded-full bottom-[-120px] right-[-120px]" />

      {/* Card */}
      <div className="glass w-full max-w-md p-8 relative z-10">

        {/* Title */}
        <h1 className="text-3xl font-bold text-white text-center">
          Gesturio
        </h1>

        <p className="text-muted text-center mt-2">
          Login to continue
        </p>

        {/* Form */}
        <form
          className="space-y-4 mt-8"
          onSubmit={(e) => {
            e.preventDefault();
            navigate("/dashboard");
          }}
        >

          {/* Email */}
          <input
            type="email"
            placeholder="Email"
            className="w-full p-3 rounded-lg bg-white/5 border border-white/10 text-white outline-none focus:border-emerald-400 transition"
          />

          {/* Password */}
          <input
            type="password"
            placeholder="Password"
            className="w-full p-3 rounded-lg bg-white/5 border border-white/10 text-white outline-none focus:border-blue-400 transition"
          />

          {/* Button */}
          <button
            type="submit"
            className="btn-primary w-full"
          >
            Login
          </button>
        </form>

        {/* Signup */}
        <p className="text-center text-muted mt-6 text-sm">
          Don’t have an account?{" "}
          <Link to="/signup" className="text-emerald-400 hover:underline">
            Sign Up
          </Link>
        </p>

      </div>
    </div>
  );
}