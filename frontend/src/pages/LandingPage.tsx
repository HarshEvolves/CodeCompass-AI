/**
 * CodeCompass — Landing Page
 *
 * A dark-themed landing page that:
 *   1. Shows the product name, tagline, and feature highlights
 *   2. Calls the backend /health endpoint on load
 *   3. Displays a live "System Status" card (connected / disconnected)
 *   4. Uses Framer Motion for smooth entrance animations
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import api from "@/lib/axios";

// ─── Types ────────────────────────────────────────────────────
/** Shape of the /health endpoint response */
interface HealthResponse {
  status: string;
  app: string;
  version: string;
}

// ─── Animation Presets ────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

const stagger = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.3 },
  },
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: { opacity: 1, scale: 1 },
};

// ─── Feature List ─────────────────────────────────────────────
const features = [
  {
    icon: "📦",
    title: "Upload Repository",
    desc: "Upload any codebase as a ZIP and let the AI analyze its structure.",
  },
  {
    icon: "🌳",
    title: "Smart Parsing",
    desc: "Tree-sitter extracts functions, classes, and imports with full context.",
  },
  {
    icon: "🔍",
    title: "Semantic Search",
    desc: "Find relevant code using natural language — not just keywords.",
  },
  {
    icon: "🤖",
    title: "AI Chat",
    desc: "Ask questions about any codebase. AI answers using only your code.",
  },
];

// ─── Component ────────────────────────────────────────────────
export default function LandingPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Call /health when the page loads
  useEffect(() => {
    const checkHealth = async () => {
      try {
        setLoading(true);
        const res = await api.get<HealthResponse>("/health");
        setHealth(res.data);
        setError(null);
      } catch (err) {
        setHealth(null);
        setError(
          err instanceof Error ? err.message : "Cannot reach backend"
        );
      } finally {
        setLoading(false);
      }
    };
    checkHealth();
  }, []);

  return (
    <div className="animated-gradient min-h-screen relative overflow-hidden">
      {/* ── Decorative background orbs ── */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div
          className="absolute top-1/4 -left-32 w-96 h-96 rounded-full opacity-20 blur-3xl animate-float"
          style={{ background: "radial-gradient(circle, #6366f1, transparent)" }}
        />
        <div
          className="absolute bottom-1/4 -right-32 w-96 h-96 rounded-full opacity-15 blur-3xl animate-float"
          style={{
            background: "radial-gradient(circle, #8b5cf6, transparent)",
            animationDelay: "3s",
          }}
        />
        <div
          className="absolute top-3/4 left-1/3 w-64 h-64 rounded-full opacity-10 blur-3xl animate-float"
          style={{
            background: "radial-gradient(circle, #ec4899, transparent)",
            animationDelay: "5s",
          }}
        />
        {/* Subtle grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(99,102,241,.3) 1px,transparent 1px)," +
              "linear-gradient(90deg,rgba(99,102,241,.3) 1px,transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      {/* ── Main Content ── */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-16">
        {/* Hero */}
        <motion.div
          className="text-center max-w-4xl mx-auto"
          variants={stagger}
          initial="hidden"
          animate="visible"
        >
          {/* Logo */}
          <motion.div variants={fadeUp} className="mb-6">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-bg-card border border-border-default animate-pulse-glow">
              <span className="text-4xl">🧭</span>
            </div>
          </motion.div>

          {/* Title */}
          <motion.h1
            variants={fadeUp}
            className="text-5xl md:text-7xl font-bold mb-6 tracking-tight"
          >
            <span className="gradient-text">CodeCompass</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            variants={fadeUp}
            className="text-xl md:text-2xl text-text-secondary mb-4 max-w-2xl mx-auto leading-relaxed"
          >
            Understand any codebase in minutes, not days.
          </motion.p>

          <motion.p
            variants={fadeUp}
            className="text-base md:text-lg text-text-muted mb-12 max-w-xl mx-auto"
          >
            Upload a repository, ask questions in plain English, and get answers
            grounded in{" "}
            <span className="text-accent font-medium">your actual code</span>
            {" "}— not generic AI knowledge.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            variants={fadeUp}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-16"
          >
            <button className="px-8 py-3.5 bg-accent hover:bg-accent-hover text-white font-semibold rounded-xl transition-all duration-300 hover:shadow-lg hover:shadow-accent/25 hover:-translate-y-0.5 cursor-pointer">
              Get Started — It's Free
            </button>
            <button className="px-8 py-3.5 bg-transparent border border-border-default hover:border-border-hover text-text-primary font-semibold rounded-xl transition-all duration-300 hover:bg-bg-card cursor-pointer">
              View on GitHub
            </button>
          </motion.div>
        </motion.div>

        {/* ── Health Status Card ── */}
        <motion.div
          variants={scaleIn}
          initial="hidden"
          animate="visible"
          transition={{ delay: 0.8, duration: 0.5 }}
          className="glass-card p-6 mb-16 w-full max-w-md"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">
              System Status
            </h3>
            {health && (
              <span className="flex items-center gap-2 text-xs text-success font-medium">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-success" />
                </span>
                Live
              </span>
            )}
          </div>

          {loading ? (
            <div className="flex items-center gap-3 text-text-muted">
              <div className="w-5 h-5 border-2 border-text-muted border-t-accent rounded-full animate-spin" />
              <span>Checking backend connection…</span>
            </div>
          ) : health ? (
            <div className="space-y-2">
              {[
                { label: "API", value: `✓ ${health.status}`, cls: "text-success" },
                { label: "App", value: health.app, cls: "font-mono text-text-primary" },
                { label: "Version", value: `v${health.version}`, cls: "font-mono text-text-primary" },
              ].map((row, i) => (
                <div
                  key={row.label}
                  className={`flex justify-between items-center py-1.5 ${
                    i < 2 ? "border-b border-border-default/50" : ""
                  }`}
                >
                  <span className="text-text-secondary text-sm">{row.label}</span>
                  <span className={`text-sm font-medium ${row.cls}`}>{row.value}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-3 text-error">
              <span className="text-lg">✕</span>
              <div>
                <p className="text-sm font-medium">Backend Unreachable</p>
                <p className="text-xs text-text-muted mt-0.5">
                  {error || "Start the backend with: cd backend && uvicorn app.main:app --reload"}
                </p>
              </div>
            </div>
          )}
        </motion.div>

        {/* ── Feature Cards ── */}
        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 max-w-5xl mx-auto w-full px-4"
          variants={stagger}
          initial="hidden"
          animate="visible"
        >
          {features.map((f) => (
            <motion.div
              key={f.title}
              variants={fadeUp}
              whileHover={{ y: -5, transition: { duration: 0.2 } }}
              className="glass-card p-6 hover:border-border-hover transition-all duration-300 group cursor-default"
            >
              <div className="text-3xl mb-4 group-hover:scale-110 transition-transform duration-300">
                {f.icon}
              </div>
              <h3 className="text-base font-semibold text-text-primary mb-2">
                {f.title}
              </h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                {f.desc}
              </p>
            </motion.div>
          ))}
        </motion.div>

        {/* ── Tech Stack ── */}
        <motion.div
          className="mt-20 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5, duration: 1 }}
        >
          <p className="text-text-muted text-xs uppercase tracking-widest mb-4">
            Powered by
          </p>
          <div className="flex flex-wrap justify-center gap-3 text-text-secondary text-sm">
            {["React", "FastAPI", "PostgreSQL", "ChromaDB", "Tree-sitter", "Gemini AI"].map(
              (tech) => (
                <span
                  key={tech}
                  className="px-4 py-1.5 rounded-full border border-border-default/50 bg-bg-card/50 hover:border-accent/30 transition-colors duration-300"
                >
                  {tech}
                </span>
              )
            )}
          </div>
        </motion.div>

        {/* ── Footer ── */}
        <motion.footer
          className="mt-16 text-text-muted text-xs"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
        >
          Phase 1 — Project Foundation ✓
        </motion.footer>
      </div>
    </div>
  );
}
