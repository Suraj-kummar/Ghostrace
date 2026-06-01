import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "./services/api";
import { Auth } from "./pages/Auth";
import { Sessions } from "./pages/Sessions";
import { SessionDetail } from "./pages/SessionDetail";
import { Settings } from "./pages/Settings";
import { 
  Activity, Sliders, LogOut, LayoutDashboard, 
  Sparkles, User 
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
      } catch (err) {
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
    // Redirect to root sessions explorer when changing projects
    if (location.pathname !== "/") {
      navigate("/");
    }
  };

  const handleProjectChangeFromSettings = (id: string) => {
    setActiveProjectId(id);
    localStorage.setItem("gr_active_project", id);
    fetchProjects(); // Reload projects list
  };

  if (!isLoggedIn) {
    return <Auth onLoginSuccess={handleLoginSuccess} />;
  }



  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="logo-icon">
            <Activity size={18} />
          </div>
          <span className="logo-text">ghostrace</span>
        </div>

        <nav>
          <ul className="nav-links">
            <li>
              <Link 
                to="/" 
                className={`nav-item ${location.pathname === "/" || location.pathname.startsWith("/sessions/") ? "active" : ""}`}
              >
                <LayoutDashboard size={16} />
                Sessions
              </Link>
            </li>
            <li>
              <Link 
                to="/settings" 
                className={`nav-item ${location.pathname === "/settings" ? "active" : ""}`}
              >
                <Sliders size={16} />
                Settings
              </Link>
            </li>
          </ul>
        </nav>

        <div className="sidebar-footer">
          <div style={styles.userInfo}>
            <User size={14} style={{ color: "var(--text-secondary)" }} />
            <span style={styles.userEmail} title={userEmail}>
              {userEmail}
            </span>
          </div>
          <button className="btn btn-secondary" onClick={handleLogout} style={styles.logoutBtn}>
            <LogOut size={14} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content body */}
      <main className="main-content">
        <header className="header-bar">
          <div className="project-select-container">
            <span style={styles.projectLabel}>Project:</span>
            {projects.length > 0 ? (
              <select 
                className="project-select" 
                value={activeProjectId} 
                onChange={handleProjectSelect}
              >
                {projects.map((proj) => (
                  <option key={proj.id} value={proj.id}>
                    {proj.name}
                  </option>
                ))}
              </select>
            ) : (
              <span style={styles.noProjectText}>No projects</span>
            )}
          </div>
          
          <div style={styles.headerRight}>
            <span className="badge badge-info" style={styles.planBadge}>
              <Sparkles size={12} style={{ marginRight: 4 }} />
              Free Plan
            </span>
          </div>
        </header>

        <div style={styles.pageBody}>
          <Routes>
            <Route 
              path="/" 
              element={<Sessions projectId={activeProjectId} />} 
            />
            <Route 
              path="/sessions/:sessionId" 
              element={<SessionDetail />} 
            />
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
  userInfo: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px",
    marginBottom: "12px",
    backgroundColor: "var(--bg-base)",
    borderRadius: "6px",
    border: "1px solid var(--border-color)",
  },
  userEmail: {
    fontSize: "12px",
    color: "var(--text-secondary)",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
    fontWeight: 500,
    flex: 1,
  },
  logoutBtn: {
    width: "100%",
    justifyContent: "center",
    padding: "8px 12px",
    fontSize: "13px",
    gap: "6px",
  },
  projectLabel: {
    fontSize: "13px",
    fontWeight: 500,
    color: "var(--text-secondary)",
  },
  noProjectText: {
    fontSize: "13px",
    color: "var(--text-muted)",
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
  },
  planBadge: {
    padding: "4px 10px",
  },
  pageBody: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    overflowY: "auto",
  },
};
