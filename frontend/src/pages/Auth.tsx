import React, { useState } from "react";
import { api } from "../services/api";
import { Activity, Lock, Mail } from "lucide-react";

interface AuthProps {
  onLoginSuccess: () => void;
}

export function Auth({ onLoginSuccess }: AuthProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

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
        setSuccess("Account created successfully! You can now log in.");
        setIsLogin(true);
        setPassword("");
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.mesh}></div>
      <div className="card glow-hover animated-fade-in" style={styles.card}>
        <div style={styles.header}>
          <div className="logo-icon" style={styles.logoIcon}>
            <Activity size={18} />
          </div>
          <span style={styles.logoText}>ghostrace</span>
        </div>

        <h2 style={styles.title}>{isLogin ? "Welcome Back" : "Get Started"}</h2>
        <p style={styles.subtitle}>
          {isLogin ? "Sign in to monitor your AI agents" : "Deploy zero-touch observability in minutes"}
        </p>

        {error && (
          <div className="badge-error" style={styles.alert}>
            {error}
          </div>
        )}

        {success && (
          <div className="badge-success" style={styles.alert}>
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} style={styles.form}>
          <div className="input-group">
            <label className="input-label" htmlFor="email">
              Email Address
            </label>
            <div style={styles.inputWrapper}>
              <Mail size={16} style={styles.inputIcon} />
              <input
                className="input-field"
                type="email"
                id="email"
                placeholder="you@domain.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={loading}
                style={styles.inputWithIcon}
              />
            </div>
          </div>

          <div className="input-group" style={{ marginBottom: 24 }}>
            <label className="input-label" htmlFor="password">
              Password
            </label>
            <div style={styles.inputWrapper}>
              <Lock size={16} style={styles.inputIcon} />
              <input
                className="input-field"
                type="password"
                id="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                style={styles.inputWithIcon}
              />
            </div>
          </div>

          <button className="btn btn-primary" type="submit" disabled={loading} style={styles.button}>
            {loading ? "Please wait..." : isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>

        <div style={styles.footer}>
          <span>{isLogin ? "Don't have an account?" : "Already have an account?"}</span>
          <button
            style={styles.toggleBtn}
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
              setSuccess("");
            }}
            disabled={loading}
          >
            {isLogin ? "Sign Up" : "Log In"}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    width: "100vw",
    backgroundColor: "var(--bg-base)",
    position: "relative",
    overflow: "hidden",
  },
  mesh: {
    position: "absolute",
    width: "600px",
    height: "600px",
    borderRadius: "50%",
    background: "radial-gradient(circle, rgba(99,102,241,0.08) 0%, rgba(9,9,11,0) 70%)",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    pointerEvents: "none",
  },
  card: {
    width: "100%",
    maxWidth: "420px",
    display: "flex",
    flexDirection: "column",
    alignItems: "stretch",
    padding: "40px",
    zIndex: 10,
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    marginBottom: "32px",
  },
  logoIcon: {
    width: "28px",
    height: "28px",
  },
  logoText: {
    fontFamily: "var(--font-heading)",
    fontWeight: 700,
    fontSize: "18px",
    letterSpacing: "-0.5px",
    color: "var(--text-primary)",
  },
  title: {
    fontFamily: "var(--font-heading)",
    fontSize: "24px",
    fontWeight: 600,
    textAlign: "center",
    marginBottom: "8px",
    color: "var(--text-primary)",
  },
  subtitle: {
    fontSize: "14px",
    color: "var(--text-secondary)",
    textAlign: "center",
    marginBottom: "24px",
  },
  form: {
    display: "flex",
    flexDirection: "column",
  },
  inputWrapper: {
    position: "relative",
    display: "flex",
    alignItems: "center",
  },
  inputIcon: {
    position: "absolute",
    left: "14px",
    color: "var(--text-muted)",
    pointerEvents: "none",
  },
  inputWithIcon: {
    paddingLeft: "42px",
    width: "100%",
  },
  button: {
    padding: "12px",
    fontSize: "15px",
  },
  alert: {
    padding: "10px 14px",
    borderRadius: "8px",
    fontSize: "13px",
    marginBottom: "20px",
    textAlign: "center",
  },
  footer: {
    display: "flex",
    justifyContent: "center",
    gap: "6px",
    fontSize: "13px",
    color: "var(--text-secondary)",
    marginTop: "24px",
  },
  toggleBtn: {
    background: "none",
    border: "none",
    color: "var(--color-primary)",
    fontWeight: 600,
    cursor: "pointer",
    padding: 0,
    outline: "none",
  },
};
