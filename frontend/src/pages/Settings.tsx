import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { Copy, Check, Plus, Key, FolderOpen, AlertTriangle } from "lucide-react";

interface SettingsProps {
  activeProjectId: string;
  onProjectChange: (projectId: string) => void;
}

export function Settings({ activeProjectId, onProjectChange }: SettingsProps) {
  const [projects, setProjects] = useState<any[]>([]);
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  
  // Project creation form
  const [newProjectName, setNewProjectName] = useState("");
  const [projectError, setProjectError] = useState("");
  const [projectLoading, setProjectLoading] = useState(false);

  // Key creation form
  const [newKeyName, setNewKeyName] = useState("");
  const [keyError, setKeyError] = useState("");
  const [keyLoading, setKeyLoading] = useState(false);
  
  // Clipboard copying state
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);
  
  // Newly generated key modal/preview
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);

  const fetchProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch (err: any) {
      console.error("Error fetching projects", err);
    }
  };

  const fetchApiKeys = async (projId: string) => {
    if (!projId) return;
    try {
      const data = await api.getApiKeys(projId);
      setApiKeys(data);
    } catch (err: any) {
      console.error("Error fetching API keys", err);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (activeProjectId) {
      fetchApiKeys(activeProjectId);
      setGeneratedKey(null); // Clear new key preview when switching projects
    }
  }, [activeProjectId]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setProjectError("");
    setProjectLoading(true);

    try {
      const project = await api.createProject(newProjectName);
      setNewProjectName("");
      await fetchProjects();
      onProjectChange(project.id); // Switch to the newly created project
    } catch (err: any) {
      setProjectError(err.message || "Could not create project.");
    } finally {
      setProjectLoading(false);
    }
  };

  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setKeyError("");
    setKeyLoading(true);
    setGeneratedKey(null);

    try {
      const key = await api.createApiKey(activeProjectId, newKeyName);
      setNewKeyName("");
      setGeneratedKey(key.key); // Display the token once to the user
      await fetchApiKeys(activeProjectId);
    } catch (err: any) {
      setKeyError(err.message || "Could not generate API key.");
    } finally {
      setKeyLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKeyId(id);
    setTimeout(() => setCopiedKeyId(null), 2000);
  };

  return (
    <div style={styles.container} className="animated-fade-in">
      <h1 style={styles.pageTitle}>Project Settings</h1>
      <p style={styles.pageSubtitle}>Manage your dashboard environments and generate python SDK keys.</p>

      <div style={styles.layoutGrid}>
        {/* Projects panel */}
        <div className="card" style={styles.panel}>
          <h2 style={styles.panelTitle}>
            <FolderOpen size={18} style={styles.panelTitleIcon} />
            Projects
          </h2>
          <p style={styles.panelDesc}>Switch between environments or spin up a new agent project namespace.</p>

          <form onSubmit={handleCreateProject} style={styles.formInline}>
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
            <button className="btn btn-primary" type="submit" disabled={projectLoading}>
              <Plus size={16} />
              Add
            </button>
          </form>

          {projectError && (
            <div className="badge-error" style={styles.errorAlert}>
              {projectError}
            </div>
          )}

          <div style={styles.list}>
            {projects.map((proj) => (
              <div
                key={proj.id}
                style={{
                  ...styles.listItem,
                  borderColor: proj.id === activeProjectId ? "var(--color-primary)" : "var(--border-color)",
                  backgroundColor: proj.id === activeProjectId ? "var(--color-primary-glow)" : "transparent",
                }}
                onClick={() => onProjectChange(proj.id)}
              >
                <div style={styles.projectInfo}>
                  <span style={styles.projectName}>{proj.name}</span>
                  <span style={styles.projectMeta}>ID: {proj.id.substring(0, 8)}...</span>
                </div>
                {proj.id === activeProjectId && (
                  <span className="badge badge-info">Active</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* API keys panel */}
        <div className="card" style={styles.panel}>
          <h2 style={styles.panelTitle}>
            <Key size={18} style={styles.panelTitleIcon} />
            API Keys
          </h2>
          <p style={styles.panelDesc}>Credentials used to authorize payload transfers from the python decorator SDK.</p>

          {activeProjectId ? (
            <>
              <form onSubmit={handleCreateApiKey} style={styles.formInline}>
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
                <button className="btn btn-primary" type="submit" disabled={keyLoading}>
                  <Plus size={16} />
                  Generate
                </button>
              </form>

              {keyError && (
                <div className="badge-error" style={styles.errorAlert}>
                  {keyError}
                </div>
              )}

              {generatedKey && (
                <div style={styles.generatedKeyBanner}>
                  <div style={styles.generatedKeyHeader}>
                    <AlertTriangle size={16} style={{ color: "var(--color-warning)" }} />
                    <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>Copy your new API Key</span>
                  </div>
                  <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "12px" }}>
                    For security reasons, this key will not be displayed again.
                  </p>
                  <div style={styles.keyDisplay}>
                    <code style={styles.keyCode}>{generatedKey}</code>
                    <button
                      className="btn btn-secondary"
                      style={styles.copyBtnInline}
                      onClick={() => copyToClipboard(generatedKey, "new_key")}
                    >
                      {copiedKeyId === "new_key" ? <Check size={14} style={{ color: "var(--color-success)" }} /> : <Copy size={14} />}
                    </button>
                  </div>
                </div>
              )}

              <div style={styles.list}>
                {apiKeys.length === 0 ? (
                  <div style={styles.emptyList}>No API Keys generated yet for this project.</div>
                ) : (
                  apiKeys.map((key) => (
                    <div key={key.id} style={styles.listItemKey}>
                      <div style={styles.keyInfo}>
                        <span style={styles.keyName}>{key.name}</span>
                        <span style={styles.keyMeta}>
                          Created: {new Date(key.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div style={styles.keyActions}>
                        <code style={styles.keyRedacted}>
                          {key.key.substring(0, 6)}••••••••••••••••••••
                        </code>
                        <button
                          className="btn btn-secondary"
                          style={styles.copyBtn}
                          onClick={() => copyToClipboard(key.key, key.id)}
                        >
                          {copiedKeyId === key.id ? (
                            <Check size={14} style={{ color: "var(--color-success)" }} />
                          ) : (
                            <Copy size={14} />
                          )}
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div style={styles.emptyList}>Please select or create a project namespace first.</div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "40px",
    display: "flex",
    flexDirection: "column",
    flex: 1,
  },
  pageTitle: {
    fontFamily: "var(--font-heading)",
    fontSize: "28px",
    fontWeight: 600,
    marginBottom: "6px",
    color: "var(--text-primary)",
  },
  pageSubtitle: {
    fontSize: "14px",
    color: "var(--text-secondary)",
    marginBottom: "32px",
  },
  layoutGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "24px",
    alignItems: "start",
  },
  panel: {
    display: "flex",
    flexDirection: "column",
    alignItems: "stretch",
    minHeight: "400px",
  },
  panelTitle: {
    fontFamily: "var(--font-heading)",
    fontSize: "18px",
    fontWeight: 600,
    marginBottom: "6px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    color: "var(--text-primary)",
  },
  panelTitleIcon: {
    color: "var(--color-primary)",
  },
  panelDesc: {
    fontSize: "13px",
    color: "var(--text-secondary)",
    marginBottom: "24px",
  },
  formInline: {
    display: "flex",
    gap: "12px",
    marginBottom: "16px",
  },
  formInput: {
    flex: 1,
    padding: "8px 12px",
  },
  errorAlert: {
    padding: "8px 12px",
    borderRadius: "6px",
    fontSize: "12px",
    marginBottom: "16px",
    textAlign: "center",
  },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    marginTop: "8px",
  },
  listItem: {
    border: "1px solid var(--border-color)",
    borderRadius: "8px",
    padding: "14px 16px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    cursor: "pointer",
    transition: "all 0.2s",
  },
  projectInfo: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  projectName: {
    fontWeight: 600,
    fontSize: "14px",
    color: "var(--text-primary)",
  },
  projectMeta: {
    fontSize: "11px",
    color: "var(--text-muted)",
  },
  listItemKey: {
    border: "1px solid var(--border-color)",
    borderRadius: "8px",
    padding: "14px 16px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "16px",
  },
  keyInfo: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  keyName: {
    fontWeight: 600,
    fontSize: "14px",
    color: "var(--text-primary)",
  },
  keyMeta: {
    fontSize: "11px",
    color: "var(--text-muted)",
  },
  keyActions: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  keyRedacted: {
    fontSize: "11px",
    color: "var(--text-muted)",
    padding: "4px 8px",
  },
  copyBtn: {
    padding: "6px 8px",
  },
  copyBtnInline: {
    padding: "8px",
    borderLeft: "none",
    borderRadius: "0 8px 8px 0",
  },
  generatedKeyBanner: {
    backgroundColor: "rgba(245, 158, 11, 0.04)",
    border: "1px dashed rgba(245, 158, 11, 0.3)",
    borderRadius: "8px",
    padding: "16px",
    marginBottom: "20px",
  },
  generatedKeyHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "13px",
    marginBottom: "6px",
  },
  keyDisplay: {
    display: "flex",
    alignItems: "stretch",
  },
  keyCode: {
    flex: 1,
    fontSize: "13px",
    backgroundColor: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    borderRadius: "8px 0 0 8px",
    padding: "10px 14px",
    color: "var(--text-primary)",
    overflowX: "auto",
    whiteSpace: "nowrap",
  },
  emptyList: {
    textAlign: "center",
    color: "var(--text-muted)",
    fontSize: "13px",
    padding: "40px 0",
  },
};
