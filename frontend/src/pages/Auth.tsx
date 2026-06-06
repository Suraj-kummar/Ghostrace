import React, { useState } from "react";
import { api } from "../services/api";
import { Activity, Lock, Mail, ArrowRight, Eye, EyeOff, Zap, Shield, TrendingUp } from "lucide-react";

interface AuthProps {
  onLoginSuccess: () => void;
}

export function Auth({ onLoginSuccess }: AuthProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Password strength meter
  const getPasswordStrength = (pwd: string): { score: number; label: string; color: string } => {
    if (pwd.length === 0) return { score: 0, label: "", color: "transparent" };
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/\d/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    const map: Record<number, { label: string; color: string }> = {
      1: { label: "Weak", color: "#ef4444" },
      2: { label: "Fair", color: "#f59e0b" },
      3: { label: "Good", color: "#3b82f6" },
      4: { label: "Strong", color: "#10b981" },
    };
    return { score, ...(map[score] || { label: "Weak", color: "#ef4444" }) };
  };
  const pwdStrength = getPasswordStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      if (isLogin) {
        await api.login(email, password);
        onLoginSuccess();
      } else {
        await api.signup(email, password);
        setSuccess("Account created! You can now sign in.");
        setIsLogin(true);
        setPassword("");
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const features = [
    { icon: <Zap size={14} />, text: "Real-time agent tracing" },
    { icon: <Shield size={14} />, text: "Zero-touch observability" },
    { icon: <TrendingUp size={14} />, text: "Token cost analytics" },
  ];

  return (
    <div style={styles.root}>
      {/* Animated aurora bg */}
      <div style={styles.aurora1} />
      <div style={styles.aurora2} />
      <div style={styles.aurora3} />
      {/* Grid overlay */}
      <div style={styles.grid} />

      <div style={styles.page}>
        {/* ── Left branding panel ── */}
        <div style={styles.leftPanel}>
          <div style={styles.brand}>
            <div style={styles.brandLogo}>
              <Activity size={22} color="white" />
            </div>
            <span style={styles.brandName}>ghostrace</span>
          </div>

          <div style={styles.heroText}>
            <h1 style={styles.heroTitle}>
              Observe every<br />
              <span style={styles.heroHighlight}>AI agent move.</span>
            </h1>
            <p style={styles.heroDesc}>
              Drop-in tracing SDK for LLM agents. Capture prompts, tokens,
              costs, tool calls, and errors — with zero config.
            </p>
          </div>

          <div style={styles.featureList}>
            {features.map((f, i) => (
              <div key={i} style={styles.featureItem}>
                <div style={styles.featureIcon}>{f.icon}</div>
                <span style={styles.featureText}>{f.text}</span>
              </div>
            ))}
          </div>

          <div style={styles.codeSnippet}>
            <span style={styles.codeComment}># One decorator. Full visibility.</span>
            <span style={styles.codeLine}>
              <span style={{ color: "#818cf8" }}>@</span>
              <span style={{ color: "#34d399" }}>trace</span>
              <span style={{ color: "#f1f1f3" }}>(api_key=</span>
              <span style={{ color: "#fbbf24" }}>"gr_…"</span>
              <span style={{ color: "#f1f1f3" }}>)</span>
            </span>
            <span style={styles.codeLine}>
              <span style={{ color: "#818cf8" }}>async def </span>
              <span style={{ color: "#38bdf8" }}>run_agent</span>
              <span style={{ color: "#f1f1f3" }}>(query):</span>
            </span>
            <span style={styles.codeLine}>
              <span style={{ color: "#a1a1aa" }}>    …</span>
            </span>
          </div>
        </div>

        {/* ── Right auth card ── */}
        <div style={styles.rightPanel}>
          <div style={styles.card} className="animated-fade-in">
            {/* Card top glow strip */}
            <div style={styles.cardGlow} />

            <div style={styles.cardHeader}>
              <h2 style={styles.cardTitle}>
                {isLogin ? "Welcome back" : "Get started"}
              </h2>
              <p style={styles.cardSub}>
                {isLogin
                  ? "Sign in to your Ghostrace dashboard"
                  : "Create your free account in seconds"}
              </p>
            </div>

            {error && (
              <div style={styles.alertError} className="animated-fade-in">
                <span style={styles.alertDot} />
                {error}
              </div>
            )}
            {success && (
              <div style={styles.alertSuccess} className="animated-fade-in">
                <span style={{ ...styles.alertDot, background: "var(--color-success)" }} />
                {success}
              </div>
            )}

            <form onSubmit={handleSubmit} style={styles.form}>
              {/* Email */}
              <div className="input-group">
                <label className="input-label" htmlFor="email">Email address</label>
                <div style={styles.inputWrap}>
                  <Mail size={15} style={styles.inputIcon} />
                  <input
                    className="input-field"
                    type="email"
                    id="email"
                    autoComplete="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    disabled={loading}
                    style={{ paddingLeft: 42 }}
                  />
                </div>
              </div>

              {/* Password */}
              <div className="input-group" style={{ marginBottom: 28 }}>
                <label className="input-label" htmlFor="password">Password</label>
                <div style={styles.inputWrap}>
                  <Lock size={15} style={styles.inputIcon} />
                  <input
                    className="input-field"
                    type={showPassword ? "text" : "password"}
                    id="password"
                    autoComplete={isLogin ? "current-password" : "new-password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    disabled={loading}
                    style={{ paddingLeft: 42, paddingRight: 42 }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={styles.eyeBtn}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
              </div>

              <button
                className="btn btn-primary"
                type="submit"
                disabled={loading}
                id={isLogin ? "login-submit-btn" : "signup-submit-btn"}
                style={styles.submitBtn}
              >
                {loading ? (
                  <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <svg width="16" height="16" viewBox="0 0 50 50" style={{ animation: "spin 0.8s linear infinite" }}>
                      <circle cx="25" cy="25" r="20" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="5" />
                      <circle cx="25" cy="25" r="20" fill="none" stroke="white" strokeWidth="5" strokeLinecap="round" strokeDasharray="80 40" />
                    </svg>
                    {isLogin ? "Signing in…" : "Creating account…"}
                  </span>
                ) : (
                  <>
                    {isLogin ? "Sign in" : "Create account"}
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>

            <div style={styles.switchRow}>
              <span style={styles.switchText}>
                {isLogin ? "Don't have an account?" : "Already have an account?"}
              </span>
              <button
                style={styles.switchBtn}
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError("");
                  setSuccess("");
                }}
                disabled={loading}
              >
                {isLogin ? "Sign up →" : "Sign in →"}
              </button>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes loading-dots {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
        .loading-dot { display:inline-block; width:6px; height:6px; border-radius:50%; background:white; animation: loading-dots 1.2s ease-in-out infinite; }
        .loading-dot:nth-child(2) { animation-delay: 0.2s; }
        .loading-dot:nth-child(3) { animation-delay: 0.4s; }
      `}</style>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  root: {
    minHeight: "100vh",
    width: "100vw",
    background: "var(--bg-base)",
    position: "relative",
    overflow: "hidden",
    display: "flex",
    alignItems: "stretch",
  },
  aurora1: {
    position: "absolute",
    width: 700, height: 700,
    borderRadius: "50%",
    background: "radial-gradient(circle, rgba(99,102,241,0.14) 0%, transparent 70%)",
    top: "-15%", left: "-10%",
    animation: "aurora-shift 18s ease-in-out infinite alternate",
    pointerEvents: "none",
  },
  aurora2: {
    position: "absolute",
    width: 500, height: 500,
    borderRadius: "50%",
    background: "radial-gradient(circle, rgba(168,85,247,0.1) 0%, transparent 70%)",
    bottom: "-10%", right: "30%",
    animation: "aurora-shift 14s ease-in-out infinite alternate-reverse",
    pointerEvents: "none",
  },
  aurora3: {
    position: "absolute",
    width: 400, height: 400,
    borderRadius: "50%",
    background: "radial-gradient(circle, rgba(56,189,248,0.07) 0%, transparent 70%)",
    top: "40%", right: "-5%",
    animation: "aurora-shift 22s ease-in-out infinite alternate",
    pointerEvents: "none",
  },
  grid: {
    position: "absolute",
    inset: 0,
    backgroundImage: "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.025) 1px, transparent 0)",
    backgroundSize: "40px 40px",
    pointerEvents: "none",
  },
  page: {
    position: "relative",
    zIndex: 1,
    display: "flex",
    width: "100%",
    minHeight: "100vh",
  },

  /* Left panel */
  leftPanel: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    padding: "60px 64px",
    gap: 40,
    borderRight: "1px solid var(--border-color)",
  },
  brand: {
    display: "flex", alignItems: "center", gap: 12,
  },
  brandLogo: {
    width: 38, height: 38,
    borderRadius: 11,
    background: "linear-gradient(135deg, #8b5cf6, #6366f1, #38bdf8)",
    display: "flex", alignItems: "center", justifyContent: "center",
    boxShadow: "0 0 24px rgba(99,102,241,0.4), 0 0 48px rgba(99,102,241,0.15)",
  },
  brandName: {
    fontFamily: "var(--font-heading)",
    fontSize: 22,
    fontWeight: 800,
    letterSpacing: "-0.5px",
    background: "linear-gradient(135deg, #f1f1f3, #818cf8)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },
  heroText: { display: "flex", flexDirection: "column", gap: 16 },
  heroTitle: {
    fontFamily: "var(--font-heading)",
    fontSize: 52,
    fontWeight: 800,
    lineHeight: 1.1,
    letterSpacing: "-1.5px",
    color: "var(--text-primary)",
  },
  heroHighlight: {
    background: "linear-gradient(135deg, #818cf8 0%, #a78bfa 50%, #38bdf8 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
  },
  heroDesc: {
    fontSize: 16,
    color: "var(--text-secondary)",
    lineHeight: 1.65,
    maxWidth: 420,
  },
  featureList: { display: "flex", flexDirection: "column", gap: 12 },
  featureItem: {
    display: "flex", alignItems: "center", gap: 12,
  },
  featureIcon: {
    width: 28, height: 28,
    borderRadius: 7,
    background: "var(--color-primary-glow)",
    border: "1px solid rgba(99,102,241,0.25)",
    display: "flex", alignItems: "center", justifyContent: "center",
    color: "var(--color-primary-light)",
    flexShrink: 0,
  },
  featureText: {
    fontSize: 14,
    color: "var(--text-secondary)",
    fontWeight: 500,
  },
  codeSnippet: {
    background: "rgba(0,0,0,0.5)",
    border: "1px solid var(--border-color)",
    borderLeft: "3px solid var(--color-primary)",
    borderRadius: "0 10px 10px 0",
    padding: "16px 20px",
    fontFamily: "var(--font-mono)",
    fontSize: 13,
    display: "flex",
    flexDirection: "column",
    gap: 4,
    maxWidth: 380,
  },
  codeComment: { color: "#52525b", fontSize: 12 },
  codeLine: { display: "flex" },

  /* Right panel */
  rightPanel: {
    width: 480,
    flexShrink: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "40px 48px",
  },
  card: {
    width: "100%",
    background: "var(--bg-card)",
    border: "1px solid var(--border-color)",
    borderRadius: 20,
    padding: "40px 36px",
    backdropFilter: "blur(20px)",
    position: "relative",
    overflow: "hidden",
    boxShadow: "0 24px 64px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.04) inset",
  },
  cardGlow: {
    position: "absolute",
    top: 0, left: "10%", right: "10%",
    height: 1,
    background: "linear-gradient(90deg, transparent, rgba(99,102,241,0.6), transparent)",
  },
  cardHeader: { marginBottom: 28 },
  cardTitle: {
    fontFamily: "var(--font-heading)",
    fontSize: 26,
    fontWeight: 700,
    color: "var(--text-primary)",
    letterSpacing: "-0.3px",
    marginBottom: 6,
  },
  cardSub: { fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.5 },

  alertError: {
    display: "flex", alignItems: "center", gap: 8,
    background: "rgba(244,63,94,0.06)",
    border: "1px solid rgba(244,63,94,0.2)",
    borderRadius: 8,
    padding: "10px 14px",
    fontSize: 13,
    color: "var(--color-error)",
    marginBottom: 20,
  },
  alertSuccess: {
    display: "flex", alignItems: "center", gap: 8,
    background: "rgba(16,185,129,0.06)",
    border: "1px solid rgba(16,185,129,0.2)",
    borderRadius: 8,
    padding: "10px 14px",
    fontSize: 13,
    color: "var(--color-success)",
    marginBottom: 20,
  },
  alertDot: {
    width: 6, height: 6, borderRadius: "50%",
    background: "var(--color-error)",
    flexShrink: 0,
  },
  form: { display: "flex", flexDirection: "column" },
  inputWrap: { position: "relative", display: "flex", alignItems: "center" },
  inputIcon: {
    position: "absolute", left: 14,
    color: "var(--text-muted)", pointerEvents: "none",
  },
  eyeBtn: {
    position: "absolute", right: 12,
    background: "none", border: "none",
    color: "var(--text-muted)", cursor: "pointer",
    display: "flex", alignItems: "center",
    transition: "color 0.2s",
  },
  submitBtn: {
    padding: "13px",
    fontSize: 15,
    width: "100%",
    justifyContent: "center",
    gap: 8,
  },
  loadingDots: {
    display: "flex", gap: 4, alignItems: "center",
  },
  switchRow: {
    marginTop: 24,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    fontSize: 13,
  },
  switchText: { color: "var(--text-secondary)" },
  switchBtn: {
    background: "none", border: "none",
    color: "var(--color-primary-light)",
    fontWeight: 700,
    cursor: "pointer",
    fontSize: 13,
    fontFamily: "var(--font-sans)",
    transition: "color 0.2s",
  },
};
