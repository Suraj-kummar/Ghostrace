import React, { useState, useEffect, useCallback } from "react";
import { api } from "../services/api";
import {
  Copy, Check, Plus, Key, FolderOpen, AlertTriangle,
  ShieldCheck, Terminal, Info, Trash2, X, AlertCircle,
  Loader
} from "lucide-react";

interface SettingsProps {
  activeProjectId: string;
  onProjectChange: (projectId: string) => void;
}

// ─── Confirm Modal ────────────────────────────────────────────────────────────
interface ConfirmModalProps {
  open: boolean;
  title: string;
  body: React.ReactNode;
  confirmLabel?: string;
  danger?: boolean;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmModal({
  open, title, body, confirmLabel = "Delete", danger = true, loading = false,
  onConfirm, onCancel,
}: ConfirmModalProps) {
  if (!open) return null;
  return (
    <div style={ms.overlay} onClick={onCancel}>
      <div style={ms.modal} className="animated-fade-in" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={ms.modalHeader}>
          <div style={{ ...ms.modalIconWrap, background: danger ? "rgba(244,63,94,0.1)" : "rgba(245,158,11,0.1)" }}>
            <AlertTriangle size={20} style={{ color: danger ? "var(--color-error)" : "var(--color-warning)" }} />
          </div>
          <div style={{ flex: 1 }}>
            <h3 style={ms.modalTitle}>{title}</h3>
          </div>
          <button style={ms.modalClose} onClick={onCancel} disabled={loading}>
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div style={ms.modalBody}>{body}</div>

        {/* Footer */}
        <div style={ms.modalFooter}>
          <button className="btn btn-secondary" onClick={onCancel} disabled={loading} style={ms.modalCancelBtn}>
            Cancel
          </button>
          <button
            className="btn"
            onClick={onConfirm}
            disabled={loading}
            style={{
              ...ms.modalConfirmBtn,
              background: danger
                ? "linear-gradient(135deg, #f43f5e, #e11d48)"
                : "linear-gradient(135deg, #f59e0b, #d97706)",
              boxShadow: danger
                ? "0 4px 16px rgba(244,63,94,0.3)"
                : "0 4px 16px rgba(245,158,11,0.3)",
            }}
          >
            {loading ? <Loader size={14} className="spin" /> : <Trash2 size={14} />}
            {loading ? "Deleting…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
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
  const [user, setUser] = useState<any>(null);
  const [userLoading, setUserLoading] = useState(false);

  // Delete modal state
  const [deleteModal, setDeleteModal] = useState<{
    open: boolean;
    type: "project" | "key";
    id: string;
    name: string;
    loading: boolean;
    error: string;
  }>({ open: false, type: "project", id: "", name: "", loading: false, error: "" });

  const fetchProjects = useCallback(async () => {
    try { setProjects(await api.getProjects()); }
    catch (e) { console.error(e); }
  }, []);

  const fetchApiKeys = useCallback(async (id: string) => {
    if (!id) return;
    try { setApiKeys(await api.getApiKeys(id)); }
    catch (e) { console.error(e); }
  }, []);

  const fetchUser = useCallback(async () => {
    setUserLoading(true);
    try { setUser(await api.getMe()); }
    catch (e) { console.error(e); }
    finally { setUserLoading(false); }
  }, []);

  useEffect(() => { fetchProjects(); fetchUser(); }, [fetchProjects, fetchUser]);
  useEffect(() => {
    if (activeProjectId) { fetchApiKeys(activeProjectId); setGeneratedKey(null); }
  }, [activeProjectId, fetchApiKeys]);

  // ── Create project ──────────────────────────────────────────────────────
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault(); setProjectError(""); setProjectLoading(true);
    try {
      const p = await api.createProject(newProjectName);
      setNewProjectName(""); await fetchProjects(); onProjectChange(p.id);
    } catch (err: any) { setProjectError(err.message || "Could not create project."); }
    finally { setProjectLoading(false); }
  };

  // ── Create API key ──────────────────────────────────────────────────────
  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault(); setKeyError(""); setKeyLoading(true); setGeneratedKey(null);
    try {
      const k = await api.createApiKey(activeProjectId, newKeyName);
      setNewKeyName(""); setGeneratedKey(k.key); await fetchApiKeys(activeProjectId);
    } catch (err: any) { setKeyError(err.message || "Could not generate key."); }
    finally { setKeyLoading(false); }
  };

  // ── Delete helpers ──────────────────────────────────────────────────────
  const openDeleteProject = (proj: any) =>
    setDeleteModal({ open: true, type: "project", id: proj.id, name: proj.name, loading: false, error: "" });

  const openDeleteKey = (key: any) =>
    setDeleteModal({ open: true, type: "key", id: key.id, name: key.name, loading: false, error: "" });

  const closeDeleteModal = () =>
    setDeleteModal(m => ({ ...m, open: false, error: "" }));

  const handleConfirmDelete = async () => {
    setDeleteModal(m => ({ ...m, loading: true, error: "" }));
    try {
      if (deleteModal.type === "project") {
        await api.deleteProject(deleteModal.id);
        closeDeleteModal();
        const remaining = projects.filter(p => p.id !== deleteModal.id);
        await fetchProjects();
        // Switch to another project or clear
        const next = remaining.find(p => p.id !== deleteModal.id);
        onProjectChange(next?.id ?? "");
      } else {
        await api.deleteApiKey(activeProjectId, deleteModal.id);
        closeDeleteModal();
        await fetchApiKeys(activeProjectId);
      }
    } catch (err: any) {
      setDeleteModal(m => ({ ...m, loading: false, error: err.message || "Delete failed." }));
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKeyId(id);
    setTimeout(() => setCopiedKeyId(null), 2000);
  };

  const activeProject = projects.find(p => p.id === activeProjectId);

  return (
    <>
      {/* ── Delete confirmation modal ── */}
      <ConfirmModal
        open={deleteModal.open}
        danger
        loading={deleteModal.loading}
        title={deleteModal.type === "project" ? "Delete project?" : "Revoke API key?"}
        confirmLabel={deleteModal.type === "project" ? "Delete project" : "Revoke key"}
        onConfirm={handleConfirmDelete}
        onCancel={closeDeleteModal}
        body={
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {deleteModal.type === "project" ? (
              <>
                <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                  You are about to permanently delete{" "}
                  <strong style={{ color: "var(--text-primary)" }}>{deleteModal.name}</strong>.
                  This will delete all sessions, trace events, and API keys associated with it.
                </p>
                <div style={ms.dangerBox}>
                  <AlertCircle size={14} style={{ color: "var(--color-error)", flexShrink: 0 }} />
                  <span>This action cannot be undone.</span>
                </div>
              </>
            ) : (
              <>
                <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                  Revoking{" "}
                  <strong style={{ color: "var(--text-primary)" }}>{deleteModal.name}</strong>{" "}
                  will immediately invalidate it. Any agents using this key will stop sending traces.
                </p>
                <div style={ms.dangerBox}>
                  <AlertCircle size={14} style={{ color: "var(--color-error)", flexShrink: 0 }} />
                  <span>SDK calls using this key will fail immediately.</span>
                </div>
              </>
            )}
            {deleteModal.error && (
              <div style={{ ...ms.dangerBox, background: "rgba(244,63,94,0.08)", border: "1px solid rgba(244,63,94,0.25)" }}>
                <AlertCircle size={14} style={{ color: "var(--color-error)", flexShrink: 0 }} />
                <span style={{ color: "var(--color-error)" }}>{deleteModal.error}</span>
              </div>
            )}
          </div>
        }
      />

      {/* ── Page ── */}
      <div style={styles.container} className="animated-fade-in">
        {/* Page header */}
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

        {/* ── Account Profile panel ── */}
        {user && (
          <div className="card" style={styles.accountCard}>
            <div style={styles.accountHeader}>
              <div style={{ ...styles.panelIcon, background: "rgba(16,185,129,0.12)" }}>
                <ShieldCheck size={16} style={{ color: "var(--color-success)" }} />
              </div>
              <div>
                <h2 style={styles.panelTitle}>Account Profile</h2>
                <p style={styles.panelDesc}>Logged in user and current subscription plan details.</p>
              </div>
            </div>
            <div style={styles.accountBody}>
              <div style={styles.accountField}>
                <span style={styles.accountFieldLabel}>Email Address</span>
                <span style={styles.accountFieldValue}>{user.email}</span>
              </div>
              <div style={styles.accountField}>
                <span style={styles.accountFieldLabel}>Subscription Plan</span>
                <span style={{ ...styles.accountFieldValue, textTransform: "uppercase", fontWeight: 700, color: "var(--color-primary-light)" }}>
                  {user.plan} Plan
                </span>
              </div>
              <div style={styles.accountField}>
                <span style={styles.accountFieldLabel}>Status</span>
                <span className="badge badge-success" style={{ fontSize: 10, alignSelf: "flex-start", marginTop: 4 }}>
                  Active
                </span>
              </div>
            </div>
          </div>
        )}

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

            {/* Create form */}
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
              <button
                className="btn btn-primary"
                type="submit"
                disabled={projectLoading}
                style={styles.addBtn}
                aria-label="Create new project"
              >
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
                    >
                      {/* Clickable project info */}
                      <div
                        style={styles.projectClickArea}
                        onClick={() => onProjectChange(proj.id)}
                        role="button"
                        tabIndex={0}
                        title={`Project ID: ${proj.id}`}
                        onKeyDown={(e) => e.key === "Enter" && onProjectChange(proj.id)}
                      >
                        <div style={{ ...styles.projectDot, background: isActive ? "var(--color-success)" : "var(--text-muted)" }} />
                        <div>
                          <span style={styles.projectName}>{proj.name}</span>
                          <code style={styles.projectId}>{proj.id.substring(0, 12)}…</code>
                        </div>
                      </div>
                      <div style={styles.projectActions}>
                        {isActive && <span className="badge badge-info" style={{ fontSize: 10 }}>Active</span>}
                        <button
                          style={styles.deleteBtn}
                          onClick={() => openDeleteProject(proj)}
                          title="Delete project"
                          aria-label={`Delete project ${proj.name}`}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
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
                  <button
                    className="btn btn-primary"
                    type="submit"
                    disabled={keyLoading}
                    style={styles.addBtn}
                    aria-label="Generate new API key"
                  >
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
                            title="Copy key"
                          >
                            {copiedKeyId === key.id
                              ? <Check size={13} style={{ color: "var(--color-success)" }} />
                              : <Copy size={13} />}
                          </button>
                          <button
                            style={styles.deleteBtn}
                            onClick={() => openDeleteKey(key)}
                            title="Revoke key"
                            aria-label={`Revoke API key ${key.name}`}
                          >
                            <Trash2 size={13} />
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

        {/* ── SDK Quick-start ── */}
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
              {
                step: 2, label: "Instrument",
                code: `from ghostrace import trace\n\n@trace(api_key="gr_YOUR_KEY")\nasync def run_agent(query): ...`,
              },
              { step: 3, label: "Run your agent — traces appear here automatically", code: null },
            ].map((s) => (
              <div key={s.step} style={styles.sdkStep}>
                <div style={styles.stepNum}>{s.step}</div>
                <div style={styles.stepBody}>
                  <span style={styles.stepLabel}>{s.label}</span>
                  {s.code && <pre style={styles.stepCode}>{s.code}</pre>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Danger Zone ── */}
        <div className="card" style={styles.dangerZoneCard}>
          <div style={styles.dangerZoneHeader}>
            <div style={{ ...styles.panelIcon, background: "rgba(244,63,94,0.12)" }}>
              <AlertTriangle size={16} style={{ color: "var(--color-error)" }} />
            </div>
            <div>
              <h2 style={styles.panelTitle}>Danger Zone</h2>
              <p style={styles.panelDesc}>Actions here are permanent and cannot be undone.</p>
            </div>
          </div>
          <div style={styles.dangerZoneBody}>
            <div style={styles.dangerZoneAction}>
              <div>
                <span style={styles.dangerZoneLabel}>Delete Account</span>
                <p style={styles.dangerZoneDesc}>
                  Permanently delete your account, projects, keys, and all session trace telemetry data.
                </p>
              </div>
              <button
                className="btn btn-secondary"
                style={styles.deleteAccountBtn}
                onClick={() => {
                  alert("Please contact support at support@ghostrace.dev to delete your account.");
                }}
              >
                Delete Account
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Error alert sub-component ────────────────────────────────────────────────
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

// ─── Modal styles ─────────────────────────────────────────────────────────────
const ms: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed", inset: 0, zIndex: 999,
    background: "rgba(0,0,0,0.6)",
    backdropFilter: "blur(6px)",
    display: "flex", alignItems: "center", justifyContent: "center",
  },
  modal: {
    background: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    borderRadius: "var(--radius-xl)",
    width: "100%", maxWidth: 440,
    boxShadow: "0 24px 64px rgba(0,0,0,0.7), 0 0 0 1px rgba(244,63,94,0.1)",
    overflow: "hidden",
  },
  modalHeader: {
    display: "flex", alignItems: "center", gap: 14,
    padding: "20px 22px 16px",
    borderBottom: "1px solid var(--border-color)",
  },
  modalIconWrap: {
    width: 40, height: 40, borderRadius: 12,
    display: "flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0,
  },
  modalTitle: {
    fontFamily: "var(--font-heading)", fontSize: 16,
    fontWeight: 700, color: "var(--text-primary)",
  },
  modalClose: {
    background: "none", border: "none", cursor: "pointer",
    color: "var(--text-muted)", padding: 4, borderRadius: 6,
    display: "flex", alignItems: "center",
    transition: "color 0.15s",
  },
  modalBody: { padding: "20px 22px" },
  modalFooter: {
    display: "flex", justifyContent: "flex-end", gap: 10,
    padding: "16px 22px",
    borderTop: "1px solid var(--border-color)",
    background: "rgba(0,0,0,0.2)",
  },
  modalCancelBtn: { padding: "9px 18px", fontSize: 13 },
  modalConfirmBtn: {
    color: "white", border: "none",
    padding: "9px 18px", fontSize: 13,
    display: "inline-flex", alignItems: "center", gap: 7,
    borderRadius: "var(--radius-md)", cursor: "pointer",
    fontFamily: "var(--font-sans)", fontWeight: 600,
    transition: "all 0.2s",
  },
  dangerBox: {
    display: "flex", alignItems: "center", gap: 8,
    background: "rgba(244,63,94,0.06)",
    border: "1px solid rgba(244,63,94,0.2)",
    borderRadius: 8, padding: "9px 12px",
    fontSize: 12, color: "var(--color-error)", fontWeight: 500,
  },
};

// ─── Page styles ──────────────────────────────────────────────────────────────
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
    transition: "all 0.18s",
  },
  projectClickArea: {
    display: "flex", alignItems: "center", gap: 10, flex: 1,
    cursor: "pointer", minWidth: 0,
  },
  projectDot: { width: 8, height: 8, borderRadius: "50%", flexShrink: 0, transition: "background 0.2s" },
  projectName: { display: "block", fontSize: 14, fontWeight: 600, color: "var(--text-primary)" },
  projectId: { display: "block", fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: 2 },
  projectActions: { display: "flex", alignItems: "center", gap: 8, flexShrink: 0 },

  deleteBtn: {
    background: "none", border: "1px solid transparent",
    borderRadius: 7, padding: "5px 7px",
    cursor: "pointer", color: "var(--text-muted)",
    display: "flex", alignItems: "center",
    transition: "all 0.15s",
  },

  keyItem: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    background: "var(--bg-glass)", border: "1px solid var(--border-color)",
    borderRadius: 10, padding: "12px 14px",
  },
  keyLeft: { display: "flex", alignItems: "center", gap: 10 },
  keyIconWrap: {
    width: 30, height: 30, borderRadius: 8,
    background: "var(--color-success-glow)", border: "1px solid rgba(16,185,129,0.2)",
    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
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

  accountCard: { padding: 24, marginBottom: 24, display: "flex", flexDirection: "column", gap: 16 },
  accountHeader: { display: "flex", alignItems: "flex-start", gap: 14 },
  accountBody: { display: "flex", gap: 32, flexWrap: "wrap" },
  accountField: { display: "flex", flexDirection: "column", gap: 4, minWidth: 150 },
  accountFieldLabel: { fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" },
  accountFieldValue: { fontSize: 14, fontWeight: 600, color: "var(--text-primary)" },

  sdkCard: { padding: 28 },
  sdkHeader: { display: "flex", alignItems: "flex-start", gap: 14, marginBottom: 24 },
  sdkSteps: { display: "flex", flexDirection: "column", gap: 20 },
  sdkStep: { display: "flex", gap: 16, alignItems: "flex-start" },
  stepNum: {
    width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
    background: "var(--color-primary-glow)", border: "1px solid rgba(99,102,241,0.3)",
    color: "var(--color-primary-light)", fontSize: 13, fontWeight: 700,
    display: "flex", alignItems: "center", justifyContent: "center", marginTop: 2,
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
