import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import {
  Copy, Check, Plus, Key, FolderOpen, AlertTriangle,
  ShieldCheck, Sparkles, Terminal, Info
} from "lucide-react";

interface SettingsProps {
  activeProjectId: string;
  onProjectChange: (projectId: string) => void;
}

export function Settings({ activeProjectId, onProjectChange }: SettingsProps) {
  const [projects, setProjects]   = useState<any[]>([]);
  const [apiKeys, setApiKeys]     = useState<any[]>([]);
  const [newProjectName, setNewProjectName] = useState("");
  const [projectError, setProjectError]     = useState("");
  const [projectLoading, setProjectLoading] = useState(false);
  const [newKeyName, setNewKeyName]   = useState("");
  const [keyError, setKeyError]       = useState("");
  const [keyLoading, setKeyLoading]   = useState(false);
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);

  const fetchProjects = async () => {
    try { setProjects(await api.getProjects()); }
    catch (e) { console.error(e); }
  };

  const fetchApiKeys = async (id: string) => {
    if (!id) return;
    try { setApiKeys(await api.getApiKeys(id)); }
    catch (e) { console.error(e); }
  };

  useEffect(() => { fetchProjects(); }, []);
  useEffect(() => { if (activeProjectId) { fetchApiKeys(activeProjectId); setGeneratedKey(null); } }, [activeProjectId]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault(); setProjectError(""); setProjectLoading(true);
    try {
      const p = await api.createProject(newProjectName);
      setNewProjectName(""); await fetchProjects(); onProjectChange(p.id);
    } catch (err: any) { setProjectError(err.message || "Could not create project."); }
    finally { setProjectLoading(false); }
  };

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault(); setKeyError(""); setKeyLoading(true); setGeneratedKey(null);
    try {
      const k = await api.createApiKey(activeProjectId, newKeyName);
      setNewKeyName(""); setGeneratedKey(k.key); await fetchApiKeys(activeProjectId);
    } catch (err: any) { setKeyError(err.message || "Could not generate key."); }
    finally { setKeyLoading(false); }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKeyId(id);
    setTimeout(() => setCopiedKeyId(null), 2000);
  };

  const activeProject = projects.find((p) => p.id === activeProjectId);

  return (
    <div style={styles.container} className="animated-fade-in">
      {/* ── Page header ── */}
      <div style={styles.pageHeader}>
        <div>
          <h1 style={styles.pageTitle}>Settings</h1>
          <p style={styles.pageSub}>Manage projects, API keys, and SDK configuration.</p>
        </div>
        {activeProject && (
          <div style={styles.activeProjectBadge}>
            <span style={styles.activeProjectDot} />
            <span style={styles.activeProjectName}>{activeProject.name}</span>
            <span style={styles.activeProjectLabel}>active workspace</span>
          </div>
        )}
      </div>

      <div style={styles.grid}>
        {/* ── Projects panel ── */}
        <div className="card" style={styles.panel}>
          <div style={styles.panelHeader}>
            <div style={styles.panelIcon}>
              <FolderOpen size={16} style={{ color: "var(--color-primary-light)" }} />
            </div>
            <div>
              <h2 style={styles.panelTitle}>Projects</h2>
              <p style={styles.panelDesc}>Separate environments for your agent deployments.</p>
            </div>
          </div>

          {/* Create project form */}
          <form onSubmit={handleCreateProject} style={styles.inlineForm}>
            <input
              className="input-field"
              type="text"
              placeholder="e.g. staging-agent"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              required
              disabled={projectLoading}
              style={styles.formInput}
            />
            <button className="btn btn-primary" type="submit" disabled={projectLoading} style={styles.addBtn} aria-label="Create new project">
              <Plus size={15} /> {projectLoading ? "…" : "Create"}
            </button>
          </form>

          {projectError && <ErrorAlert msg={projectError} />}

          {/* Projects list */}
          <div style={styles.list}>
            {projects.length === 0 ? (
              <div style={styles.emptyList}>No projects yet.</div>
            ) : (
              projects.map((proj) => {
                const isActive = proj.id === activeProjectId;
                return (
                  <div
                    key={proj.id}
                    style={{
                      ...styles.listItem,
                      borderColor: isActive ? "rgba(99,102,241,0.4)" : "var(--border-color)",
                      background: isActive ? "var(--color-primary-glow2)" : "var(--bg-glass)",
                      boxShadow: isActive ? "0 0 0 1px rgba(99,102,241,0.15) inset" : "none",
                    }}
                    onClick={() => onProjectChange(proj.id)}
                    role="button"
                    tabIndex={0}
                    title={`Project ID: ${proj.id}`}
                    onKeyDown={(e) => e.key === "Enter" && onProjectChange(proj.id)}
                  >
                    <div style={styles.projectInfoWrap}>
                      <div style={{ ...styles.projectDot, background: isActive ? "var(--color-success)" : "var(--text-muted)" }} />
                      <div>
                        <span style={styles.projectName}>{proj.name}</span>
                        <code style={styles.projectId}>{proj.id.substring(0, 12)}…</code>
                      </div>
                    </div>
                    {isActive && <span className="badge badge-info" style={{ fontSize: 10 }}>Active</span>}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* ── API Keys panel ── */}
        <div className="card" style={styles.panel}>
          <div style={styles.panelHeader}>
            <div style={{ ...styles.panelIcon, background: "rgba(56,189,248,0.12)" }}>
              <Key size={16} style={{ color: "var(--color-info)" }} />
            </div>
            <div>
              <h2 style={styles.panelTitle}>API Keys</h2>
              <p style={styles.panelDesc}>Authorize the Python SDK to send trace payloads.</p>
            </div>
          </div>

          {activeProjectId ? (
            <>
              <form onSubmit={handleCreateApiKey} style={styles.inlineForm}>
                <input
                  className="input-field"
                  type="text"
                  placeholder="e.g. production-key"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  required
                  disabled={keyLoading}
                  style={styles.formInput}
                />
                <button className="btn btn-primary" type="submit" disabled={keyLoading} style={styles.addBtn} aria-label="Generate new API key">
                  <Plus size={15} /> {keyLoading ? "…" : "Generate"}
                </button>
              </form>

              {keyError && <ErrorAlert msg={keyError} />}

              {/* New key reveal banner */}
              {generatedKey && (
                <div style={styles.newKeyBanner} className="animated-fade-in">
                  <div style={styles.newKeyHeader}>
                    <AlertTriangle size={14} style={{ color: "var(--color-warning)", flexShrink: 0 }} />
                    <span style={{ fontWeight: 700, color: "var(--text-primary)", fontSize: 13 }}>
                      Save this key — it won't be shown again
                    </span>
                  </div>
                  <div style={styles.newKeyRow}>
                    <code style={styles.newKeyCode}>{generatedKey}</code>
                    <button
                      className="btn btn-secondary"
                      style={styles.copyInlineBtn}
                      onClick={() => copyToClipboard(generatedKey, "new_key")}
                    >
                      {copiedKeyId === "new_key"
                        ? <Check size={13} style={{ color: "var(--color-success)" }} />
                        : <Copy size={13} />}
                    </button>
                  </div>
                </div>
              )}

              {/* Keys list */}
              <div style={styles.list}>
                {apiKeys.length === 0 ? (
                  <div style={styles.emptyList}>No keys yet. Generate one above.</div>
                ) : (
                  apiKeys.map((key) => (
                    <div key={key.id} style={styles.keyItem}>
                      <div style={styles.keyLeft}>
                        <div style={styles.keyIconWrap}>
                          <ShieldCheck size={14} style={{ color: "var(--color-success)" }} />
                        </div>
                        <div>
                          <span style={styles.keyName}>{key.name}</span>
                          <span style={styles.keyDate}>Created {new Date(key.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div style={styles.keyRight}>
                        <code style={styles.keyRedacted}>{key.key.substring(0, 8)}••••••••</code>
                        <button
                          className="btn btn-secondary"
                          style={styles.copyBtn}
                          onClick={() => copyToClipboard(key.key, key.id)}
                        >
                          {copiedKeyId === key.id
                            ? <Check size={13} style={{ color: "var(--color-success)" }} />
                            : <Copy size={13} />}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div style={styles.emptyList}>Select a project to manage its API keys.</div>
          )}
        </div>
      </div>

      {/* ── SDK Quick-start card ── */}
      <div className="card" style={styles.sdkCard}>
        <div style={styles.sdkHeader}>
          <div style={{ ...styles.panelIcon, background: "rgba(168,85,247,0.12)" }}>
            <Terminal size={16} style={{ color: "#c084fc" }} />
          </div>
          <div>
            <h2 style={styles.panelTitle}>SDK Quick-start</h2>
            <p style={styles.panelDesc}>Get traces flowing in under 60 seconds.</p>
          </div>
        </div>

        <div style={styles.sdkSteps}>
          {[
            { step: 1, label: "Install", code: "pip install ghostrace" },
            { step: 2, label: "Instrument", code: `from ghostrace import trace\n\n@trace(api_key="gr_YOUR_KEY")\nasync def run_agent(query): ...` },
            { step: 3, label: "Run your agent — traces appear here automatically", code: null },
          ].map((s) => (
            <div key={s.step} style={styles.sdkStep}>
              <div style={styles.stepNum}>{s.step}</div>
              <div style={styles.stepBody}>
                <span style={styles.stepLabel}>{s.label}</span>
                {s.code && (
                  <pre style={styles.stepCode}>{s.code}</pre>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ErrorAlert({ msg }: { msg: string }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      background: "rgba(244,63,94,0.06)", border: "1px solid rgba(244,63,94,0.2)",
      borderRadius: 8, padding: "9px 14px", fontSize: 13,
      color: "var(--color-error)", marginBottom: 14,
    }}>
      <Info size={13} style={{ flexShrink: 0 }} />
      {msg}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: { padding: "36px 40px", display: "flex", flexDirection: "column", gap: 28, flex: 1 },
  pageHeader: { display: "flex", alignItems: "flex-start", justifyContent: "space-between" },
  pageTitle: {
    fontFamily: "var(--font-heading)", fontSize: 30, fontWeight: 700, letterSpacing: "-0.5px",
    background: "linear-gradient(135deg, var(--text-primary), var(--text-secondary))",
    WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
    marginBottom: 6,
  },
  pageSub: { fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.5 },
  activeProjectBadge: {
    display: "flex", alignItems: "center", gap: 8,
    background: "var(--bg-glass)", border: "1px solid var(--border-color)",
    borderRadius: 10, padding: "10px 16px",
  },
  activeProjectDot: { width: 7, height: 7, borderRadius: "50%", background: "var(--color-success)", boxShadow: "0 0 6px var(--color-success)" },
  activeProjectName: { fontWeight: 700, fontSize: 14, color: "var(--text-primary)" },
  activeProjectLabel: { fontSize: 11, color: "var(--text-muted)", marginLeft: 4 },

  grid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, alignItems: "start" },
  panel: { display: "flex", flexDirection: "column", gap: 0, minHeight: 380, padding: 24 },
  panelHeader: { display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 20 },
  panelIcon: {
    width: 36, height: 36, borderRadius: 10,
    background: "var(--color-primary-glow)",
    display: "flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0,
  },
  panelTitle: { fontFamily: "var(--font-heading)", fontSize: 16, fontWeight: 700, color: "var(--text-primary)", marginBottom: 3 },
  panelDesc: { fontSize: 12, color: "var(--text-secondary)" },

  inlineForm: { display: "flex", gap: 10, marginBottom: 14 },
  formInput: { flex: 1, fontSize: 13, height: 40 },
  addBtn: { padding: "0 16px", height: 40, gap: 6, fontSize: 13, flexShrink: 0 },

  list: { display: "flex", flexDirection: "column", gap: 8, marginTop: 4 },
  emptyList: { textAlign: "center", color: "var(--text-muted)", fontSize: 13, padding: "32px 0" },

  listItem: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    border: "1px solid", borderRadius: 10, padding: "12px 14px",
    cursor: "pointer", transition: "all 0.18s",
  },
  projectInfoWrap: { display: "flex", alignItems: "center", gap: 10 },
  projectDot: { width: 8, height: 8, borderRadius: "50%", flexShrink: 0, transition: "background 0.2s" },
  projectName: { display: "block", fontSize: 14, fontWeight: 600, color: "var(--text-primary)" },
  projectId: { display: "block", fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: 2 },

  keyItem: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    background: "var(--bg-glass)", border: "1px solid var(--border-color)",
    borderRadius: 10, padding: "12px 14px",
  },
  keyLeft: { display: "flex", alignItems: "center", gap: 10 },
  keyIconWrap: {
    width: 30, height: 30, borderRadius: 8,
    background: "var(--color-success-glow)",
    border: "1px solid rgba(16,185,129,0.2)",
    display: "flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0,
  },
  keyName: { display: "block", fontSize: 13, fontWeight: 600, color: "var(--text-primary)" },
  keyDate: { display: "block", fontSize: 11, color: "var(--text-muted)", marginTop: 2 },
  keyRight: { display: "flex", alignItems: "center", gap: 8 },
  keyRedacted: { fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)", padding: "4px 8px", background: "rgba(0,0,0,0.3)", borderRadius: 5 },
  copyBtn: { padding: "6px 9px", gap: 0 },

  newKeyBanner: {
    background: "rgba(245,158,11,0.05)", border: "1px solid rgba(245,158,11,0.25)",
    borderRadius: 10, padding: 14, marginBottom: 14,
    display: "flex", flexDirection: "column", gap: 10,
  },
  newKeyHeader: { display: "flex", alignItems: "center", gap: 8 },
  newKeyRow: { display: "flex", alignItems: "stretch" },
  newKeyCode: {
    flex: 1, fontFamily: "var(--font-mono)", fontSize: 12,
    background: "var(--bg-surface)", border: "1px solid var(--border-color)",
    borderRight: "none", borderRadius: "8px 0 0 8px", padding: "9px 12px",
    color: "var(--text-primary)", overflowX: "auto", whiteSpace: "nowrap",
  },
  copyInlineBtn: { padding: "0 14px", borderRadius: "0 8px 8px 0", borderLeft: "none" },

  sdkCard: { padding: 28 },
  sdkHeader: { display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 24 },
  sdkSteps: { display: "flex", flexDirection: "column", gap: 20 },
  sdkStep: { display: "flex", gap: 16, alignItems: "flex-start" },
  stepNum: {
    width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
    background: "var(--color-primary-glow)", border: "1px solid rgba(99,102,241,0.3)",
    color: "var(--color-primary-light)", fontSize: 13, fontWeight: 700,
    display: "flex", alignItems: "center", justifyContent: "center",
    marginTop: 2,
  },
  stepBody: { display: "flex", flexDirection: "column", gap: 8, flex: 1 },
  stepLabel: { fontSize: 14, fontWeight: 600, color: "var(--text-primary)" },
  stepCode: {
    background: "rgba(0,0,0,0.45)", border: "1px solid var(--border-color)",
    borderLeft: "3px solid var(--color-primary)",
    borderRadius: "0 8px 8px 0", padding: "12px 16px",
    fontFamily: "var(--font-mono)", fontSize: 12, color: "#c4c4d4",
    whiteSpace: "pre", overflowX: "auto", lineHeight: 1.6,
  },
};
