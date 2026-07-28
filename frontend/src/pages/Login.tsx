import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "@/lib/axios";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await api.post("/auth/login", { email, password });
      const { access_token } = response.data;
      
      // Store token locally and redirect
      localStorage.setItem("access_token", access_token);
      navigate("/dashboard");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Authentication failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animated-gradient min-h-screen flex items-center justify-center p-4">
      <div className="glass-card w-full max-w-md p-8 relative overflow-hidden">
        {/* Decorative ambient background */}
        <div className="absolute -top-10 -left-10 w-40 h-40 rounded-full bg-accent opacity-15 blur-2xl pointer-events-none" />
        <div className="absolute -bottom-10 -right-10 w-40 h-40 rounded-full bg-accent-secondary opacity-15 blur-2xl pointer-events-none" />

        <div className="text-center mb-8 relative z-10">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-bg-card border border-border-default mb-4">
            <span className="text-2xl">🧭</span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-text-primary mb-2">
            Welcome Back
          </h2>
          <p className="text-sm text-text-secondary">
            Sign in to continue exploring your codebases.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-error/10 border border-error/20 text-error text-sm text-left animate-pulse-glow">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1.5 text-left">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full px-4 py-2.5 bg-bg-secondary border border-border-default rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors duration-200"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1.5 text-left">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-2.5 bg-bg-secondary border border-border-default rounded-lg text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent transition-colors duration-200"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-accent hover:bg-accent-hover disabled:bg-accent/50 text-white font-semibold rounded-lg transition-all duration-200 hover:shadow-lg hover:shadow-accent/25 cursor-pointer flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Signing in...</span>
              </>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-text-secondary relative z-10">
          Don't have an account?{" "}
          <Link to="/register" className="text-accent hover:text-accent-hover font-medium underline transition-colors">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
