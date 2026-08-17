import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { FaCheckCircle, FaTimesCircle } from "react-icons/fa";

export default function Signup() {
  const navigate = useNavigate();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const passwordRules = {
    length: password.length >= 8 && password.length <= 15,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[@$!%*?&]/.test(password),
  };

  const validatePassword = (pwd) => {
    return (
      pwd.length >= 8 &&
      pwd.length <= 15 &&
      /[A-Z]/.test(pwd) &&
      /[a-z]/.test(pwd) &&
      /\d/.test(pwd) &&
      /[@$!%*?&]/.test(pwd)
    );
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validatePassword(password)) {
      setError("Please satisfy all password requirements.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setError("");
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b1220] relative overflow-hidden px-4">

      {/* Background Glow */}
      <div className="absolute w-[500px] h-[500px] bg-emerald-500/10 blur-[120px] rounded-full top-[-120px] left-[-120px]" />
      <div className="absolute w-[500px] h-[500px] bg-blue-500/10 blur-[120px] rounded-full bottom-[-120px] right-[-120px]" />

      {/* Card */}
      <div className="glass w-full max-w-md p-8 relative z-10">

        {/* Title */}
        <h1 className="text-3xl font-bold text-white text-center">
          Gesturio
        </h1>

        <p className="text-muted text-center mt-2">
          Create your account
        </p>

        <form onSubmit={handleSubmit} className="space-y-4 mt-8">

          {/* Full Name */}
          <input
            type="text"
            placeholder="Full Name"
            required
            className="w-full p-3 rounded-lg bg-white/5 border border-white/10 text-white outline-none focus:border-emerald-400 transition"
          />

          {/* Email */}
          <input
            type="email"
            placeholder="Email Address"
            required
            className="w-full p-3 rounded-lg bg-white/5 border border-white/10 text-white outline-none focus:border-blue-400 transition"
          />

          {/* Password */}
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full p-3 rounded-lg bg-white/5 border border-white/10 text-white outline-none focus:border-emerald-400 transition"
          />

          {/* Confirm Password */}
          <input
            type="password"
            placeholder="Confirm Password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            className="w-full p-3 rounded-lg bg-white/5 border border-white/10 text-white outline-none focus:border-blue-400 transition"
          />

          {/* Password Rules */}
          <div className="glass p-4 text-sm">

            <p className="text-white font-semibold mb-3">
              Password Requirements
            </p>

            <div className="space-y-2 text-muted">

              <div className="flex items-center gap-2">
                {passwordRules.length ? (
                  <FaCheckCircle className="text-green-400" />
                ) : (
                  <FaTimesCircle className="text-red-400" />
                )}
                8 - 15 characters
              </div>

              <div className="flex items-center gap-2">
                {passwordRules.uppercase ? (
                  <FaCheckCircle className="text-green-400" />
                ) : (
                  <FaTimesCircle className="text-red-400" />
                )}
                One uppercase letter
              </div>

              <div className="flex items-center gap-2">
                {passwordRules.lowercase ? (
                  <FaCheckCircle className="text-green-400" />
                ) : (
                  <FaTimesCircle className="text-red-400" />
                )}
                One lowercase letter
              </div>

              <div className="flex items-center gap-2">
                {passwordRules.number ? (
                  <FaCheckCircle className="text-green-400" />
                ) : (
                  <FaTimesCircle className="text-red-400" />
                )}
                One number
              </div>

              <div className="flex items-center gap-2">
                {passwordRules.special ? (
                  <FaCheckCircle className="text-green-400" />
                ) : (
                  <FaTimesCircle className="text-red-400" />
                )}
                One special character
              </div>

            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500 rounded-lg p-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Button */}
          <button type="submit" className="btn-primary w-full">
            Create Account
          </button>

        </form>

        {/* Login Link */}
        <p className="text-center text-muted mt-6 text-sm">
          Already have an account?{" "}
          <Link to="/" className="text-emerald-400 hover:underline">
            Login
          </Link>
        </p>

      </div>
    </div>
  );
}