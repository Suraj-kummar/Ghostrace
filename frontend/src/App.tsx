import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "./services/api";
import { Auth } from "./pages/Auth";
import { Sessions } from "./pages/Sessions";
import { SessionDetail } from "./pages/SessionDetail";
import { Settings } from "./pages/Settings";
import {
  Activity, Sliders, LogOut, LayoutDashboard,
  Sparkles, User, ChevronDown, Zap
} from "lucide-react";
import "./App.css";

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(api.isLoggedIn());
  const [projects, setProjects] = useState<any[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string>("");
  const [userEmail, setUserEmail] = useState<string>("");

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    getUserInfo();
  };

  const handleLogout = () => {
    api.logout();
    setIsLoggedIn(false);
    setProjects([]);
    setActiveProjectId("");
    setUserEmail("");
    navigate("/");
  };

  const getUserInfo = () => {
    const token = localStorage.getItem("gr_token");
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setUserEmail(payload.sub || "user@ghostrace.dev");
      } catch {
        setUserEmail("user@ghostrace.dev");
      }
    }
  };

  const fetchProjects = async () => {
    if (!isLoggedIn) return;
    try {
      const data = await api.getProjects();
      setProjects(data);
      if (data.length > 0) {
        const savedProj = localStorage.getItem("gr_active_project");
        const exists = data.some((p: any) => p.id === savedProj);
        if (savedProj && exists) {
          setActiveProjectId(savedProj);
        } else {
          setActiveProjectId(data[0].id);
          localStorage.setItem("gr_active_project", data[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load projects", err);
    }
  };

  useEffect(() => {
    if (isLoggedIn) {
      getUserInfo();
      fetchProjects();
    }
  }, [isLoggedIn]);

  const handleProjectSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setActiveProjectId(id);
    localStorage.setItem("gr_active_project", id);
    if (location.pathname !== "/") navigate("/");
  };

  const handleProjectChangeFromSettings = (id: string) => {
    setActiveProjectId(id);
    localStorage.setItem("gr_active_project", id);
    fetchProjects();
  };

  if (!isLoggedIn) {
    return <Auth onLoginSuccess={handleLoginSuccess} />;
  }

  const navItems = [
    { to: "/", icon: <LayoutDashboard size={16} />, label: "Sessions", match: (p: string) => p === "/" || p.startsWith("/sessions/") },
    { to: "/settings", icon: <Sliders size={16} />, label: "Settings", match: (p: string) => p === "/settings" },
  ];

  const activeProject = projects.find((p) => p.id === activeProjectId);

  return (
    <div className="app-container">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">
            <Activity size={17} />
          </div>
          <span className="logo-text">ghostrace</span>
        </div>

        {/* Project switcher pill */}
        {activeProject && (
          <div style={styles.projectPill}>
            <span style={styles.projectPillDot} />
            <span style={styles.projectPillName}>{activeProject.name}</span>
            <ChevronDown size={12} style={{ color: "var(--text-muted)", marginLeft: "auto" }} />
          </div>
        )}

        <nav style={{ marginTop: 12 }}>
          <ul className="nav-links">
            {navItems.map((item) => (
              <li key={item.to}>
                <Link
                  to={item.to}
                  className={`nav-item${item.match(location.pathname) ? " active" : ""}`}
                >
                  {item.icon}
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* Status indicator */}
        <div style={styles.statusRow}>
          <div className="dot dot-success" />
          <span style={styles.statusText}>All systems operational</span>
        </div>

        <div className="sidebar-footer">
          <div style={styles.userCard}>
            <div style={styles.userAvatar}>
              {userEmail.charAt(0).toUpperCase()}
            </div>
            <div style={styles.userDetails}>
              <span style={styles.userEmailText} title={userEmail}>
                {userEmail.length > 20 ? userEmail.substring(0, 18) + "…" : userEmail}
              </span>
              <span style={styles.userPlan}>Free plan</span>
            </div>
          </div>
          <button className="btn btn-secondary" onClick={handleLogout} style={styles.logoutBtn} aria-label="Sign out of your account">
            <LogOut size={14} />
            Sign out
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="main-content">
        {/* Header bar */}
        <header className="header-bar">
          <div className="project-select-container">
            <span style={styles.headerLabel}>Workspace</span>
            {projects.length > 0 ? (
              <select
                className="project-select"
                value={activeProjectId}
                onChange={handleProjectSelect}
              >
                {projects.map((proj) => (
                  <option key={proj.id} value={proj.id}>{proj.name}</option>
                ))}
              </select>
            ) : (
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>No projects</span>
            )}
          </div>

          <div style={styles.headerRight}>
            <div style={styles.liveBadge}>
              <div className="dot dot-success" style={{ width: 6, height: 6 }} />
              <span>Live</span>
            </div>
            <span className="badge badge-purple" style={styles.planBadge}>
              <Sparkles size={11} style={{ marginRight: 4 }} />
              Free Plan
            </span>
            <div style={styles.headerUser}>
              <User size={14} style={{ color: "var(--text-muted)" }} />
            </div>
          </div>
        </header>

        {/* Page content */}
        <div style={styles.pageBody}>
          <Routes>
            <Route path="/" element={<Sessions projectId={activeProjectId} />} />
            <Route path="/sessions/:sessionId" element={<SessionDetail />} />
            <Route
              path="/settings"
              element={
                <Settings
                  activeProjectId={activeProjectId}
                  onProjectChange={handleProjectChangeFromSettings}
                />
              }
            />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

const styles: Record<string, React.CSSProperties> = {
  projectPill: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "8px 12px",
    background: "var(--bg-glass)",
    border: "1px solid var(--border-color)",
    borderRadius: "var(--radius-md)",
    fontSize: 12,
    fontWeight: 500,
    color: "var(--text-secondary)",
    cursor: "pointer",
    marginBottom: 4,
  },
  projectPillDot: {
    width: 6, height: 6,
    borderRadius: "50%",
    background: "var(--color-success)",
    boxShadow: "0 0 6px var(--color-success)",
    flexShrink: 0,
  },
  projectPillName: {
    fontWeight: 600,
    color: "var(--text-primary)",
    fontSize: 13,
    flex: 1,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  statusRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    padding: "10px 14px",
    marginTop: "auto",
    marginBottom: 4,
  },
  statusText: {
    fontSize: 11,
    color: "var(--text-muted)",
    fontWeight: 500,
  },
  userCard: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "10px 12px",
    background: "var(--bg-glass)",
    border: "1px solid var(--border-color)",
    borderRadius: "var(--radius-md)",
    marginBottom: 10,
  },
  userAvatar: {
    width: 30, height: 30,
    borderRadius: "50%",
    background: "linear-gradient(135deg, #6366f1, #a855f7)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "white",
    fontSize: 13,
    fontWeight: 700,
    flexShrink: 0,
  },
  userDetails: {
    display: "flex",
    flexDirection: "column",
    gap: 2,
    overflow: "hidden",
  },
  userEmailText: {
    fontSize: 12,
    fontWeight: 600,
    color: "var(--text-primary)",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  userPlan: {
    fontSize: 10,
    color: "var(--text-muted)",
    fontWeight: 500,
  },
  logoutBtn: {
    width: "100%",
    padding: "9px 14px",
    fontSize: 13,
    gap: 8,
    justifyContent: "center",
  },
  headerLabel: {
    fontSize: 12,
    fontWeight: 600,
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: 12,
  },
  liveBadge: {
    display: "flex",
    alignItems: "center",
    gap: 6,
    fontSize: 12,
    fontWeight: 600,
    color: "var(--color-success)",
    background: "var(--color-success-glow)",
    border: "1px solid rgba(16,185,129,0.2)",
    borderRadius: 99,
    padding: "3px 10px",
  },
  planBadge: {
    padding: "4px 10px",
  },
  headerUser: {
    width: 32, height: 32,
    borderRadius: "50%",
    background: "var(--bg-glass)",
    border: "1px solid var(--border-color)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
  },
  pageBody: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    overflowY: "auto",
  },
};
