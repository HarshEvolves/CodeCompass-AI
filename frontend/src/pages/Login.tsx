import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Mail, Lock, Compass, ArrowRight, ShieldAlert, Code2, Database, BrainCircuit, Sparkles } from "lucide-react";
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
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-bg-primary text-text-primary font-sans relative overflow-hidden">
      {/* Top ambient glow circles */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-accent opacity-[0.04] blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-15%] w-[600px] h-[600px] rounded-full bg-accent-secondary opacity-[0.04] blur-[160px] pointer-events-none" />

      {/* Left panel - Visual Showcase (60% width) */}
      <div className="hidden lg:flex lg:col-span-7 relative flex-col justify-between p-16 bg-[#09090B] border-r border-border-default overflow-y-auto">
        <div className="max-w-[620px] mx-auto w-full flex flex-col justify-between h-full">
          
          {/* Branding header (Perfect left alignment alignment) */}
          <div className="flex items-center gap-3 select-none mb-12">
            <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center shadow-lg shadow-accent/20">
              <Compass className="w-5.5 h-5.5 text-white" />
            </div>
            <span className="font-bold tracking-tight text-base text-text-primary">
              CodeCompass AI
            </span>
          </div>

          {/* Hero & Dashboard Showcase Container */}
          <div className="space-y-12 text-left">
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="space-y-4"
            >
              <h1 className="text-5xl font-extrabold tracking-tight leading-[1.1] select-none text-text-primary">
                Explore your codebases <br />
                <span className="gradient-text font-bold">semantically.</span>
              </h1>
              <p className="text-base text-text-secondary leading-relaxed max-w-[560px] select-none">
                CodeCompass parses, chunks, and indexes your repositories, letting you run grounded AI chats with precise line-range citations.
              </p>
            </motion.div>

            {/* Premium Dashboard Preview Mockup (Built with pure UI code) */}
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="w-full bg-[#121215] border border-border-default rounded-2xl overflow-hidden shadow-2xl relative select-none"
            >
              {/* Title Bar */}
              <div className="bg-[#18181B] px-4 py-3 border-b border-border-default flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-error opacity-80" />
                  <div className="w-3 h-3 rounded-full bg-warning opacity-80" />
                  <div className="w-3 h-3 rounded-full bg-success opacity-80" />
                </div>
                <div className="text-[10px] font-mono text-text-muted">workspace/ReplayIQ-main</div>
                <div className="w-12" />
              </div>

              {/* Window Content */}
              <div className="grid grid-cols-12 h-[220px] text-xs">
                {/* Mock sidebar (col-span-4) */}
                <div className="col-span-4 bg-[#0E0E11] p-4 border-r border-border-default/50 space-y-4">
                  <div className="space-y-1">
                    <div className="text-[9px] font-bold text-text-muted uppercase tracking-wider">Explorer</div>
                    <div className="text-[10px] text-accent font-semibold py-1.5 px-2 bg-accent/5 rounded-lg border border-accent/10 truncate">
                      📦 ReplayIQ-main
                    </div>
                  </div>
                  <div className="space-y-1.5 font-mono text-[9px] text-text-secondary text-left pl-2">
                    <div className="text-text-primary">📂 app</div>
                    <div className="pl-3 text-text-muted">📂 core</div>
                    <div className="pl-3 text-accent font-semibold">📄 security.py</div>
                    <div className="pl-3">📂 services</div>
                    <div>📂 tests</div>
                  </div>
                </div>

                {/* Mock Chat Viewport (col-span-8) */}
                <div className="col-span-8 p-4 flex flex-col justify-between bg-[#121215]">
                  <div className="space-y-3.5 overflow-y-auto">
                    <div className="flex justify-end">
                      <div className="bg-accent text-white px-3 py-2 rounded-2xl rounded-tr-sm text-[11px] max-w-[85%] text-left">
                        Where is verify_password defined?
                      </div>
                    </div>
                    <div className="flex justify-start">
                      <div className="bg-[#18181B] border border-border-default/80 px-3 py-2 rounded-2xl rounded-tl-sm text-[10px] text-text-secondary text-left space-y-1.5 max-w-[90%]">
                        <p>In <span className="text-accent font-semibold font-mono">app/core/security.py</span>:</p>
                        <pre className="bg-bg-primary/80 p-2 rounded-lg font-mono text-[9px] text-text-primary border border-border-default/40">
                          def verify_password(plain, hashed):
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Feature Grid cards (2x2) with generous spacing */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 select-none">
              {[
                {
                  icon: <Code2 className="w-5.5 h-5.5 text-accent" />,
                  title: "⚡ Semantic Parsing",
                  desc: "Tree-sitter powered AST architecture mapping.",
                },
                {
                  icon: <BrainCircuit className="w-5.5 h-5.5 text-[#C084FC]" />,
                  title: "🧠 Smart Chunking",
                  desc: "AST-aware semantic segment generator.",
                },
                {
                  icon: <Database className="w-5.5 h-5.5 text-success" />,
                  title: "🔍 Vector Search",
                  desc: "ChromaDB vector similarity coordinates lookup.",
                },
                {
                  icon: <Sparkles className="w-5.5 h-5.5 text-[#FB7185]" />,
                  title: "💬 AI Chat",
                  desc: "Strict citation-grounded RAG query cycles.",
                },
              ].map((feature, idx) => (
                <div
                  key={idx}
                  className="saas-card p-6 bg-[#121215] border border-border-default/60 rounded-2xl flex items-start gap-4 h-full"
                >
                  <div className="p-2.5 rounded-xl bg-bg-primary border border-border-default shrink-0">
                    {feature.icon}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-text-primary">{feature.title}</h4>
                    <p className="text-[11px] text-text-secondary mt-1.5 leading-relaxed">{feature.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Footer info (Perfect bottom alignment) */}
          <div className="text-xs text-text-muted select-none mt-16 pt-6 border-t border-border-default/30 text-left">
            © {new Date().getFullYear()} CodeCompass AI. Sandbox deployment.
          </div>
        </div>
      </div>

      {/* Right panel - Form Workspace (40% width, centered card) */}
      <div className="col-span-1 lg:col-span-5 flex flex-col justify-center items-center py-12 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-[480px] bg-[#18181B]/80 backdrop-blur-xl border border-border-default rounded-[20px] p-10 shadow-2xl relative text-left"
        >
          {/* Header block (mb-8 ~ 32px spacing) */}
          <div className="mb-8 select-none">
            {/* Logo header for mobile screens */}
            <div className="flex items-center gap-2.5 justify-center sm:justify-start lg:hidden mb-6">
              <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center">
                <Compass className="w-4.5 h-4.5 text-white" />
              </div>
              <span className="font-bold tracking-tight text-text-primary">
                CodeCompass AI
              </span>
            </div>

            <h2 className="text-2xl font-bold tracking-tight text-text-primary">
              Welcome back
            </h2>
            <p className="text-xs text-text-secondary mt-2">
              Enter your credentials to access your workspace.
            </p>
          </div>

          {/* Error Notice (mb-8 ~ 32px spacing) */}
          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mb-8 flex items-start gap-3 p-4 rounded-xl bg-error/10 border border-error/15 text-error text-xs leading-relaxed"
            >
              <ShieldAlert className="w-4.5 h-4.5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </motion.div>
          )}

          {/* Form Fields container */}
          <form onSubmit={handleSubmit}>
            {/* Email Address */}
            <div className="mb-6">
              <label className="block text-xs font-bold uppercase tracking-wider text-text-secondary mb-2 select-none">
                Email Address
              </label>
              {/* Flexbox row with borderless input to guarantee icon never overlaps text */}
              <div className="flex items-center bg-bg-primary border border-border-default rounded-xl h-[52px] focus-within:border-accent focus-within:ring-3 focus-within:ring-accent-glow transition-all overflow-hidden px-4">
                <Mail className="w-5 h-5 text-text-muted shrink-0 mr-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="flex-1 h-full bg-transparent border-0 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
                />
              </div>
            </div>

            {/* Password */}
            <div className="mb-8">
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold uppercase tracking-wider text-text-secondary select-none">
                  Password
                </label>
                <span className="text-[10px] font-semibold text-accent hover:text-accent-secondary cursor-pointer select-none">
                  Forgot password?
                </span>
              </div>
              {/* Flexbox row with borderless input to guarantee icon never overlaps text */}
              <div className="flex items-center bg-bg-primary border border-border-default rounded-xl h-[52px] focus-within:border-accent focus-within:ring-3 focus-within:ring-accent-glow transition-all overflow-hidden px-4">
                <Lock className="w-5 h-5 text-text-muted shrink-0 mr-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="flex-1 h-full bg-transparent border-0 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
                />
              </div>
            </div>

            {/* Gradient Continue Button (52px height) */}
            <button
              type="submit"
              disabled={loading}
              className="w-full h-[52px] bg-gradient-to-r from-accent to-accent-hover disabled:from-accent/40 disabled:to-accent-hover/40 text-white font-semibold text-sm rounded-xl transition-all cursor-pointer flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-accent/15 mb-6"
            >
              {loading ? (
                <>
                  <div className="w-4.5 h-4.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <span>Continue</span>
                  <ArrowRight className="w-4.5 h-4.5" />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative flex items-center justify-center my-6 select-none">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border-default" />
            </div>
            <span className="relative px-3 bg-[#18181B] text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Or
            </span>
          </div>

          {/* Sign Up Link */}
          <p className="text-center text-xs text-text-secondary select-none">
            Don't have an account?{" "}
            <Link
              to="/register"
              className="text-accent hover:text-text-primary font-semibold underline underline-offset-4 transition-colors"
            >
              Sign up
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
