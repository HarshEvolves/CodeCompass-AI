import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
  Mail,
  Lock,
  Compass,
  ArrowRight,
  ShieldAlert,
  Sparkles,
  Code2,
  BrainCircuit,
  Database,
  FileCode2,
  Boxes,
  UserRound,
} from "lucide-react";
import api from "@/lib/axios";

const CODE_SNIPPET = `async def index_repository_chunks(repo_id: UUID) -> int:
    chunks = await load_chunks(repo_id)
    model = get_embedding_model()

    embeddings = await loop.run_in_executor(
        None, lambda: model.encode(
            [c.content for c in chunks]
        )
    )

    collection.upsert(
        ids=[c.id for c in chunks],
        embeddings=embeddings,
    )
    return len(chunks)`;

const FEATURES = [
  {
    icon: Code2,
    title: "Semantic Parsing",
    desc: "Tree-sitter powered AST architecture mapping.",
    tint: "text-accent",
  },
  {
    icon: BrainCircuit,
    title: "Smart Chunking",
    desc: "AST-aware semantic segment generation.",
    tint: "text-[#C084FC]",
  },
  {
    icon: Database,
    title: "Vector Search",
    desc: "ChromaDB similarity lookup across your codebase.",
    tint: "text-success",
  },
  {
    icon: Sparkles,
    title: "AI Chat",
    desc: "Citation-grounded answers rooted in your code.",
    tint: "text-[#FB7185]",
  },
];

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [guestLoading, setGuestLoading] = useState(false);
  const shouldReduceMotion = useReducedMotion();

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

  // Continue as Guest logs into a single shared demo account (not a new user
  // per visit), so any repositories or data seen here are shared/public and
  // should never be used for anything sensitive.
  const handleGuestLogin = async () => {
    setError(null);
    setGuestLoading(true);

    try {
      const response = await api.post("/auth/guest");
      const { access_token } = response.data;
      localStorage.setItem("access_token", access_token);
      navigate("/dashboard");
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not start a guest session. Please try again.");
    } finally {
      setGuestLoading(false);
    }
  };

  // Entrance animation preset: honors prefers-reduced-motion by dropping the
  // slide offset and shortening the transition instead of disabling it outright.
  const fadeUp = (delay = 0) =>
    shouldReduceMotion
      ? { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { duration: 0.3, delay } }
      : {
          initial: { opacity: 0, y: 18 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.55, delay, ease: [0.16, 1, 0.3, 1] as const },
        };

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary font-sans relative overflow-hidden">
      {/* Ambient background: subtle grid + gradient orbs, no hard divider */}
      <div
        className="absolute inset-0 opacity-[0.05] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(to right, #FFFFFF 1px, transparent 1px), linear-gradient(to bottom, #FFFFFF 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          maskImage: "radial-gradient(ellipse 80% 60% at 50% 0%, black 40%, transparent 100%)",
        }}
      />
      <div className="absolute top-[-15%] left-[-8%] w-[600px] h-[600px] rounded-full bg-accent opacity-[0.10] blur-[160px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[650px] h-[650px] rounded-full bg-[#C084FC] opacity-[0.08] blur-[170px] pointer-events-none" />
      <div className="absolute top-[35%] right-[18%] w-[350px] h-[350px] rounded-full bg-accent-secondary opacity-[0.07] blur-[140px] pointer-events-none" />

      <div className="relative z-10 min-h-screen flex flex-col lg:flex-row">
        {/* Left panel - Showcase */}
        <div className="hidden lg:flex lg:w-[58%] xl:w-[60%] flex-col justify-between px-16 xl:px-20 py-14">
          <div className="max-w-[620px] w-full flex flex-col justify-between h-full mx-auto">
            {/* Branding header */}
            <motion.div {...fadeUp(0)} className="flex items-center gap-3 select-none mb-14">
              <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center shadow-lg shadow-accent/25">
                <Compass className="w-5.5 h-5.5 text-white" />
              </div>
              <span className="font-bold tracking-tight text-base text-text-primary">CodeCompass AI</span>
            </motion.div>

            <div className="space-y-10 text-left">
              {/* Hero */}
              <motion.div {...fadeUp(0.05)} className="space-y-5">
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/10 border border-accent/20 text-[11px] font-semibold text-accent-secondary select-none">
                  <Sparkles className="w-3.5 h-3.5" />
                  AI-powered code intelligence
                </div>
                <h1 className="text-5xl font-extrabold tracking-tight leading-[1.08] select-none text-text-primary">
                  Understand any codebase
                  <br />
                  <span className="gradient-text">in seconds, not sprints.</span>
                </h1>
                <p className="text-[15px] text-text-secondary leading-relaxed max-w-[480px] select-none">
                  CodeCompass parses, chunks, and indexes your repositories, then answers questions with
                  precise, citation-backed line references.
                </p>
              </motion.div>

              {/* Dynamic code-intelligence visualization */}
              <motion.div {...fadeUp(0.15)} className="relative">
                <div className="w-full bg-[#0D0D10] border border-border-default rounded-2xl overflow-hidden shadow-2xl select-none">
                  <div className="bg-[#141417] px-4 py-3 border-b border-border-default flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-error/70" />
                      <div className="w-2.5 h-2.5 rounded-full bg-warning/70" />
                      <div className="w-2.5 h-2.5 rounded-full bg-success/70" />
                    </div>
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-text-muted">
                      <FileCode2 className="w-3 h-3" />
                      embedder.py
                    </div>
                    <div className="w-12" />
                  </div>
                  <SyntaxHighlighter
                    language="python"
                    style={vscDarkPlus}
                    showLineNumbers
                    wrapLines
                    customStyle={{
                      margin: 0,
                      padding: "18px 12px",
                      background: "transparent",
                      fontSize: "11.5px",
                      lineHeight: "1.7",
                    }}
                  >
                    {CODE_SNIPPET}
                  </SyntaxHighlighter>
                </div>

                {/* Floating metadata badges */}
                <motion.div
                  {...fadeUp(0.5)}
                  animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: [0, -6, 0] }}
                  transition={
                    shouldReduceMotion
                      ? { duration: 0.3, delay: 0.5 }
                      : { duration: 4, delay: 0.9, repeat: Infinity, ease: "easeInOut" }
                  }
                  className="absolute top-3 right-3 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-bg-card/95 border border-border-default shadow-xl text-[10px] font-mono text-text-secondary"
                >
                  <Boxes className="w-3 h-3 text-accent" />
                  1,842 chunks indexed
                </motion.div>
                <motion.div
                  {...fadeUp(0.6)}
                  animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: [0, -6, 0] }}
                  transition={
                    shouldReduceMotion
                      ? { duration: 0.3, delay: 0.6 }
                      : { duration: 4.5, delay: 1.1, repeat: Infinity, ease: "easeInOut" }
                  }
                  className="absolute bottom-3 left-3 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-bg-card/95 border border-border-default shadow-xl text-[10px] font-mono text-text-secondary"
                >
                  <FileCode2 className="w-3 h-3 text-success" />
                  247 files parsed
                </motion.div>
              </motion.div>

              {/* Feature grid: compact glass cards with hover lift */}
              <motion.div {...fadeUp(0.3)} className="grid grid-cols-2 gap-3 select-none pt-2">
                {FEATURES.map((feature) => (
                  <div
                    key={feature.title}
                    className="glass-effect rounded-xl p-4 flex items-start gap-3 transition-all duration-300 hover:border-accent/30 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-accent/5"
                  >
                    <div className="p-2 rounded-lg bg-bg-primary border border-border-default shrink-0">
                      <feature.icon className={`w-4 h-4 ${feature.tint}`} />
                    </div>
                    <div>
                      <h4 className="text-[13px] font-semibold text-text-primary">{feature.title}</h4>
                      <p className="text-[11px] text-text-secondary mt-1 leading-relaxed">{feature.desc}</p>
                    </div>
                  </div>
                ))}
              </motion.div>
            </div>

            {/* Footer */}
            <div className="text-xs text-text-muted select-none mt-14 pt-6 border-t border-border-default/30 text-left">
              © {new Date().getFullYear()} CodeCompass AI. Sandbox deployment.
            </div>
          </div>
        </div>

        {/* Right panel - Login form */}
        <div className="flex-1 flex flex-col justify-center items-center px-6 py-12 lg:py-0">
          <motion.div
            {...fadeUp(0.1)}
            className="w-full max-w-[440px] bg-bg-card/70 backdrop-blur-2xl border border-border-default rounded-[24px] p-8 sm:p-10 shadow-2xl relative text-left"
          >
            {/* Mobile logo */}
            <div className="flex items-center gap-2.5 justify-center lg:hidden mb-8 select-none">
              <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center">
                <Compass className="w-4.5 h-4.5 text-white" />
              </div>
              <span className="font-bold tracking-tight text-text-primary">CodeCompass AI</span>
            </div>

            <div className="mb-8 select-none">
              <h2 className="text-2xl font-bold tracking-tight text-text-primary">Welcome back</h2>
              <p className="text-[13px] text-text-secondary mt-2">
                Sign in to continue exploring your workspace.
              </p>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="mb-6 flex items-start gap-3 p-4 rounded-xl bg-error/10 border border-error/15 text-error text-xs leading-relaxed"
              >
                <ShieldAlert className="w-4.5 h-4.5 shrink-0 mt-0.5" />
                <span>{error}</span>
              </motion.div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="mb-5">
                <label htmlFor="login-email" className="block text-xs font-semibold text-text-secondary mb-2 select-none">
                  Email address
                </label>
                <div className="flex items-center bg-bg-primary/60 border border-border-default rounded-xl h-[50px] focus-within:border-accent focus-within:ring-3 focus-within:ring-accent-glow transition-all overflow-hidden px-4">
                  <Mail className="w-4.5 h-4.5 text-text-muted shrink-0 mr-3" />
                  <input
                    id="login-email"
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="flex-1 h-full bg-transparent border-0 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
                  />
                </div>
              </div>

              <div className="mb-7">
                <div className="flex justify-between items-center mb-2">
                  <label htmlFor="login-password" className="text-xs font-semibold text-text-secondary select-none">
                    Password
                  </label>
                  <span className="text-[11px] font-medium text-accent hover:text-accent-secondary cursor-pointer select-none transition-colors">
                    Forgot password?
                  </span>
                </div>
                <div className="flex items-center bg-bg-primary/60 border border-border-default rounded-xl h-[50px] focus-within:border-accent focus-within:ring-3 focus-within:ring-accent-glow transition-all overflow-hidden px-4">
                  <Lock className="w-4.5 h-4.5 text-text-muted shrink-0 mr-3" />
                  <input
                    id="login-password"
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="flex-1 h-full bg-transparent border-0 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
                  />
                </div>
              </div>

              <motion.button
                type="submit"
                disabled={loading}
                whileHover={shouldReduceMotion || loading ? undefined : { scale: 1.01 }}
                whileTap={shouldReduceMotion || loading ? undefined : { scale: 0.99 }}
                className="w-full h-[50px] bg-gradient-to-r from-accent to-accent-hover disabled:from-accent/40 disabled:to-accent-hover/40 text-white font-semibold text-sm rounded-xl transition-shadow cursor-pointer flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-accent/20 mb-5"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <span>Continue</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </motion.button>
            </form>

            <div className="relative flex items-center justify-center my-5 select-none">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border-default" />
              </div>
              <span className="relative px-3 bg-bg-card text-[10px] font-semibold uppercase tracking-wider text-text-muted">
                Or
              </span>
            </div>

            <motion.button
              type="button"
              onClick={handleGuestLogin}
              disabled={guestLoading}
              whileHover={shouldReduceMotion || guestLoading ? undefined : { scale: 1.01 }}
              whileTap={shouldReduceMotion || guestLoading ? undefined : { scale: 0.99 }}
              className="w-full h-[50px] bg-accent/5 border border-accent/20 disabled:opacity-40 text-text-primary font-semibold text-sm rounded-xl transition-colors cursor-pointer flex items-center justify-center gap-2 hover:bg-accent/10 hover:border-accent/30 mb-6"
            >
              {guestLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-text-primary border-t-transparent rounded-full animate-spin" />
                  <span>Starting guest session...</span>
                </>
              ) : (
                <>
                  <UserRound className="w-4 h-4 text-accent-secondary" />
                  <span>Continue as Guest</span>
                </>
              )}
            </motion.button>

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
    </div>
  );
}
