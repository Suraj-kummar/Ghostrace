import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import {
  Search, Database, DollarSign, Clock, AlertCircle,
  ChevronRight, RefreshCw, BarChart2, Tag, TrendingUp, Zap, RotateCcw
} from "lucide-react";

interface SessionsProps {
  projectId: string;
}

export function Sessions({ projectId }: SessionsProps) {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [page, setPage] = useState(0);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [exportingId, setExportingId] = useState<string | null>(null);
  const PAGE_SIZE = 20;

  const fetchSessions = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const data = await api.getSessions(projectId);
      setSessions(data);
    } catch (err) {
      console.error("Error fetching sessions", err);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const handleDelete = async (sessionId: string) => {
    if (!window.confirm("Delete this session permanently?")) return;
    setDeletingId(sessionId);
    try {
      await api.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
    } catch (err) {
      console.error("Delete failed", err);
    } finally {
      setDeletingId(null);
    }
  };

  const handleExport = async (sessionId: string) => {
    setExportingId(sessionId);
    try {
      const resp = await fetch(`/api/sessions/${sessionId}/export`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
      });
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `session-${sessionId.substring(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed", err);
    } finally {
      setExportingId(null);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [projectId]);

  // Show friendly prompt when no project has been selected yet
  if (!projectId) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, gap: 12, padding: 60 }}>
        <p style={{ fontSize: 15, color: "var(--text-muted)", textAlign: "center" }}>
          Select or create a project in <b style={{ color: "var(--text-secondary)" }}>Settings</b> to start viewing sessions.
        </p>
      </div>
    );
  }

  let totalCost = 0, totalTokens = 0, totalLatency = 0,
    latencyCount = 0, errorCount = 0;

  sessions.forEach((s) => {
    let sessionHasError = false;
    s.events?.forEach((e: any) => {
      if (e.event_type === "error" || e.error_type) sessionHasError = true;
      if (e.cost_usd) totalCost += e.cost_usd;
      if (e.tokens_in) totalTokens += e.tokens_in;
      if (e.tokens_out) totalTokens += e.tokens_out;
      if (e.latency_ms) { totalLatency += e.latency_ms; latencyCount++; }
    });
    if (sessionHasError) errorCount++;
  });

  const avgLatency = latencyCount > 0 ? Math.round(totalLatency / latencyCount) : 0;

  const filteredSessions = sessions.filter((s) => {
    const tags = s.tags ?? {};
    const matchesSearch =
      s.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.name && s.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      Object.keys(tags).some(
        (key) =>
          key.toLowerCase().includes(searchTerm.toLowerCase()) ||
          String(tags[key]).toLowerCase().includes(searchTerm.toLowerCase())
      );
    if (!matchesSearch) return false;
    const sessionHasError = s.events?.some((e: any) => e.event_type === "error" || e.error_type);
    if (filterType === "error") return sessionHasError;
    if (filterType === "success") return !sessionHasError;
    return true;
  });

  const totalPages = Math.ceil(filteredSessions.length / PAGE_SIZE);
  const pagedSessions = filteredSessions.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const formatTokens = (n: number) => {
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}m`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
    return n.toString();
  };
  const formatCost = (n: number) => {
    if (n === 0) return "$0.00";
    if (n < 0.01) return `$${n.toFixed(4)}`;
    return `$${n.toFixed(2)}`;
  };
  const formatLatency = (ms: number) => {
    if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
    return `${ms}ms`;
  };

  const metrics = [
    {
      icon: <BarChart2 size={18} />,
      iconColor: "#818cf8",
      iconBg: "rgba(99,102,241,0.12)",
      label: "Total Sessions",
      value: sessions.length.toString(),
      sub: errorCount > 0 ? `${errorCount} errored` : "All clean",
      subColor: errorCount > 0 ? "var(--color-error)" : "var(--color-success)",
    },
    {
      icon: <DollarSign size={18} />,
      iconColor: "#34d399",
      iconBg: "rgba(16,185,129,0.12)",
      label: "Total Cost",
      value: formatCost(totalCost),
      sub: "All models combined",
      subColor: "var(--text-muted)",
    },
    {
      icon: <Database size={18} />,
      iconColor: "#38bdf8",
      iconBg: "rgba(56,189,248,0.12)",
      label: "Total Tokens",
      value: formatTokens(totalTokens),
      sub: "Prompt + Output",
      subColor: "var(--text-muted)",
    },
    {
      icon: <Clock size={18} />,
      iconColor: "#fbbf24",
      iconBg: "rgba(245,158,11,0.12)",
      label: "Avg Latency",
      value: formatLatency(avgLatency),
      sub: "Per trace execution",
      subColor: "var(--text-muted)",
    },
  ];

  return (
    <div style={styles.container} className="animated-fade-in">
      {/* ── Page header ── */}
      <div style={styles.pageHeader}>
        <div>
          <h1 style={styles.pageTitle}>Sessions Explorer</h1>
          <p style={styles.pageSub}>
            Monitor agent runs, trace token costs, latencies, and error states.
          </p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={fetchSessions}
          disabled={loading}
          style={styles.refreshBtn}
        >
          <RefreshCw size={14} className={loading ? "spin" : ""} />
          Refresh
        </button>
      </div>

      {/* ── Metric cards ── */}
      <div style={styles.metricsGrid}>
        {metrics.map((m, i) => (
          <div
            key={i}
            className="card"
            style={{ ...styles.metricCard, animationDelay: `${i * 60}ms` }}
          >
            {/* Colored top stripe */}
            <div style={{ ...styles.metricAccent, background: m.iconColor, opacity: 0.7 }} />
            <div style={styles.metricBody}>
              <div style={{ ...styles.metricIconWrap, background: m.iconBg }}>
                <span style={{ color: m.iconColor }}>{m.icon}</span>
              </div>
              <div style={styles.metricInfo}>
                <span style={styles.metricLabel}>{m.label}</span>
                <span style={styles.metricValue}>{m.value}</span>
                <span style={{ ...styles.metricSub, color: m.subColor }}>{m.sub}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Filters ── */}
      <div style={styles.filtersBar}>
        <div style={styles.searchWrapper}>
          <Search size={15} style={styles.searchIcon} />
          <input
            className="input-field"
            type="text"
            placeholder="Search by name, ID, or tags…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={styles.searchInput}
          />
        </div>

        <div style={styles.filterGroup}>
          {["all", "success", "error"].map((f) => (
            <button
              key={f}
              style={{
                ...styles.filterBtn,
                background: filterType === f ? "var(--color-primary-glow)" : "transparent",
                color: filterType === f ? "var(--color-primary-light)" : "var(--text-secondary)",
                borderColor: filterType === f ? "rgba(99,102,241,0.3)" : "transparent",
              }}
              onClick={() => setFilterType(f)}
            >
              {f === "all" ? "All runs" : f === "success" ? "✓ Success" : "✗ Errors"}
            </button>
          ))}
        </div>
      </div>

      {/* ── Table ── */}
      <div className="card" style={styles.tableCard}>
        {/* Table header */}
        <div style={styles.tableHeader}>
          <span style={styles.tableHeaderCell}>Session</span>
          <span style={styles.tableHeaderCell}>Status / Loops</span>
          <span style={styles.tableHeaderCell}>Tags</span>
          <span style={styles.tableHeaderCell}>Events</span>
          <span style={styles.tableHeaderCell}>Tokens</span>
          <span style={styles.tableHeaderCell}>Cost</span>
          <span style={styles.tableHeaderCell}>Duration</span>
          <span style={{ ...styles.tableHeaderCell, textAlign: "right" }}>Actions</span>
        </div>

        {/* Rows */}
        <div style={styles.tableBody}>
          {loading ? (
            /* Skeleton loading rows */
            [...Array(4)].map((_, i) => (
              <div key={i} style={styles.skeletonRow}>
                {[40, 15, 20, 8, 12, 10, 12, 10].map((w, j) => (
                  <div key={j} className="skeleton" style={{ width: `${w}%`, height: 14, borderRadius: 6 }} />
                ))}
              </div>
            ))
            filteredSessions.length === 0 ? (
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>
                <Zap size={28} style={{ color: "var(--text-muted)" }} />
              </div>
              <p style={styles.emptyTitle}>No sessions found</p>
              <p style={styles.emptyDesc}>
                {sessions.length === 0
                  ? "Instrument your agents with the SDK to start capturing traces."
                  : "Try adjusting your search or filter."}
              </p>
            </div>
          ) : (
            pagedSessions.map((session, idx) => {
              const sessionHasError = session.events?.some(
                (e: any) => e.event_type === "error" || e.error_type
              );
              let sessionCost = 0, sessionTokens = 0, sessionLatency = 0;
              session.events?.forEach((e: any) => {
                if (e.cost_usd) sessionCost += e.cost_usd;
                if (e.tokens_in) sessionTokens += e.tokens_in;
                if (e.tokens_out) sessionTokens += e.tokens_out;
                if (e.latency_ms) sessionLatency += e.latency_ms;
              });

              return (
                <div
                  key={session.id}
                  style={{
                    ...styles.tableRow,
                    animationDelay: `${idx * 30}ms`,
                  }}
                  className="animated-fade-in"
                >
                  {/* Session name/id */}
                  <div style={styles.tableCell}>
                    <Link to={`/sessions/${session.id}`} style={styles.sessionLink}>
                      <span style={styles.sessionName}>{session.name || "Unnamed Session"}</span>
                      <code style={styles.sessionId} title={session.id}>{session.id.substring(0, 18)}…</code>
                    </Link>
                  </div>

                  {/* Status + Loop badge */}
                  <div style={{ ...styles.tableCell, flexDirection: "column", alignItems: "flex-start", gap: 5 }}>
                    {sessionHasError ? (
                      <span className="badge badge-error" style={{ gap: 5 }}>
                        <AlertCircle size={11} />
                        Error
                      </span>
                    ) : (
                      <span className="badge badge-success" style={{ gap: 5 }}>
                        <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--color-success)", display: "inline-block" }} />
                        Success
                      </span>
                    )}
                    {session.loop_detected && (
                      <span className="badge badge-warning" style={{ gap: 4, fontSize: 10 }}>
                        <RotateCcw size={9} />
                        Loop
                      </span>
                    )}
                  </div>

                  {/* Tags */}
                  <div style={styles.tableCell}>
                    <div style={styles.tagsRow}>
                      {Object.entries(session.tags ?? {}).slice(0, 2).map(([k, v]) => (
                        <span key={k} style={styles.tagChip}>
                          <Tag size={9} />
                          {k}:{String(v)}
                        </span>
                      ))}
                      {Object.keys(session.tags ?? {}).length > 2 && (
                        <span style={styles.tagMore}>
                          +{Object.keys(session.tags ?? {}).length - 2}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Events */}
                  <div style={styles.tableCell}>
                    <span style={styles.numValue}>{session.events?.length || 0}</span>
                  </div>

                  {/* Tokens */}
                  <div style={styles.tableCell}>
                    <span style={styles.numValue}>{formatTokens(sessionTokens)}</span>
                  </div>

                  {/* Cost */}
                  <div style={styles.tableCell}>
                    <span style={{ ...styles.numValue, color: "var(--color-success)" }}>
                      {formatCost(sessionCost)}
                    </span>
                  </div>

                  {/* Duration */}
                  <div style={styles.tableCell}>
                    <span style={styles.numValue}>
                      {session.duration_ms != null
                        ? formatLatency(session.duration_ms)
                        : formatLatency(sessionLatency)}
                    </span>
                  </div>

                  {/* Actions */}
                  <div style={{ ...styles.tableCell, textAlign: "right", gap: 6 }}>
                    <Link
                      to={`/sessions/${session.id}`}
                      className="btn btn-secondary"
                      style={styles.inspectBtn}
                    >
                      Inspect
                      <ChevronRight size={13} />
                    </Link>
                    <button
                      title="Export JSON"
                      disabled={exportingId === session.id}
                      onClick={() => handleExport(session.id)}
                      style={{ ...styles.inspectBtn, background: 'rgba(56,189,248,0.1)', border: '1px solid rgba(56,189,248,0.2)', color: '#38bdf8', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', borderRadius: 7, padding: '6px 10px', fontSize: 12 }}
                    >
                      ⬇
                    </button>
                    <button
                      title="Delete session"
                      disabled={deletingId === session.id}
                      onClick={() => handleDelete(session.id)}
                      style={{ ...styles.inspectBtn, background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', borderRadius: 7, padding: '6px 10px', fontSize: 12 }}
                    >
                      🗑
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, padding: '12px 24px', borderTop: '1px solid var(--border-color)' }}>
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)} style={{ padding: '6px 14px', borderRadius: 7, border: '1px solid var(--border-color)', background: 'var(--bg-glass)', color: 'var(--text-secondary)', cursor: page === 0 ? 'default' : 'pointer', opacity: page === 0 ? 0.4 : 1 }}>← Prev</button>
            <span style={{ padding: '6px 12px', color: 'var(--text-muted)', fontSize: 13 }}>{page + 1} / {totalPages}</span>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} style={{ padding: '6px 14px', borderRadius: 7, border: '1px solid var(--border-color)', background: 'var(--bg-glass)', color: 'var(--text-secondary)', cursor: page >= totalPages - 1 ? 'default' : 'pointer', opacity: page >= totalPages - 1 ? 0.4 : 1 }}>Next →</button>
          </div>
        )}

        {/* Footer count */}
        {!loading && filteredSessions.length > 0 && (
          <div style={styles.tableFooter}>
            <span>
              Showing <b>{pagedSessions.length}</b> of <b>{filteredSessions.length}</b> sessions
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "36px 40px",
    display: "flex",
    flexDirection: "column",
    flex: 1,
    gap: 28,
  },
  pageHeader: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },
  pageTitle: {
    fontFamily: "var(--font-heading)",
    fontSize: 30,
    fontWeight: 700,
    letterSpacing: "-0.5px",
    background: "linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
    marginBottom: 6,
  },
  pageSub: {
    fontSize: 14,
    color: "var(--text-secondary)",
    lineHeight: 1.5,
  },
  refreshBtn: {
    gap: 8,
    padding: "9px 16px",
    fontSize: 13,
  },
  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 18,
  },
  metricCard: {
    padding: 0,
    overflow: "hidden",
    cursor: "default",
    position: "relative",
  },
  metricAccent: {
    position: "absolute",
    top: 0, left: 0, right: 0,
    height: 2,
    borderRadius: "14px 14px 0 0",
  } as React.CSSProperties,
  metricBody: {
    display: "flex",
    gap: 16,
    alignItems: "center",
    padding: "20px 22px",
  },
  metricIconWrap: {
    width: 44, height: 44,
    borderRadius: 10,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  metricInfo: {
    display: "flex",
    flexDirection: "column",
    gap: 3,
  },
  metricLabel: {
    fontSize: 11,
    fontWeight: 600,
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.6px",
  },
  metricValue: {
    fontFamily: "var(--font-heading)",
    fontSize: 26,
    fontWeight: 700,
    color: "var(--text-primary)",
    lineHeight: 1.15,
  },
  metricSub: {
    fontSize: 11,
    fontWeight: 500,
  },
  filtersBar: {
    display: "flex",
    alignItems: "center",
    gap: 16,
  },
  searchWrapper: {
    position: "relative",
    flex: 1,
    maxWidth: 440,
    display: "flex",
    alignItems: "center",
  },
  searchIcon: {
    position: "absolute",
    left: 14,
    color: "var(--text-muted)",
    pointerEvents: "none",
  },
  searchInput: {
    paddingLeft: 42,
    fontSize: 13,
    height: 40,
  },
  filterGroup: {
    display: "flex",
    background: "var(--bg-glass)",
    border: "1px solid var(--border-color)",
    borderRadius: 10,
    padding: 4,
    gap: 2,
  },
  filterBtn: {
    padding: "6px 16px",
    fontSize: 12,
    fontWeight: 600,
    border: "1px solid transparent",
    borderRadius: 8,
    cursor: "pointer",
    transition: "all 0.15s",
    outline: "none",
    fontFamily: "var(--font-sans)",
    letterSpacing: "0.1px",
  },
  tableCard: {
    padding: 0,
    overflow: "hidden",
  },
  tableHeader: {
    display: "grid",
    gridTemplateColumns: "2.5fr 1fr 1.5fr 0.7fr 1fr 0.9fr 1fr 1fr",
    padding: "12px 24px",
    borderBottom: "1px solid var(--border-color)",
    background: "rgba(0,0,0,0.2)",
  },
  tableHeaderCell: {
    fontSize: 11,
    fontWeight: 700,
    color: "var(--text-muted)",
    textTransform: "uppercase",
    letterSpacing: "0.6px",
  },
  tableBody: {
    display: "flex",
    flexDirection: "column",
  },
  tableRow: {
    display: "grid",
    gridTemplateColumns: "2.5fr 1fr 1.5fr 0.7fr 1fr 0.9fr 1fr 1fr",
    padding: "0 24px",
    borderBottom: "1px solid var(--border-color)",
    alignItems: "center",
    transition: "background 0.15s",
    minHeight: 60,
  },
  skeletonRow: {
    display: "grid",
    gridTemplateColumns: "2.5fr 1fr 1.5fr 0.7fr 1fr 0.9fr 1fr 1fr",
    padding: "16px 24px",
    borderBottom: "1px solid var(--border-color)",
    alignItems: "center",
    gap: 8,
  },
  tableCell: {
    display: "flex",
    alignItems: "center",
    padding: "0 6px",
  },
  sessionLink: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
    textDecoration: "none",
  },
  sessionName: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--text-primary)",
  },
  sessionId: {
    fontSize: 11,
    color: "var(--text-muted)",
    fontFamily: "var(--font-mono)",
  },
  numValue: {
    fontSize: 13,
    fontWeight: 600,
    color: "var(--text-secondary)",
    fontFamily: "var(--font-mono)",
  },
  tagsRow: {
    display: "flex",
    gap: 5,
    flexWrap: "wrap",
  },
  tagChip: {
    display: "inline-flex",
    alignItems: "center",
    gap: 4,
    background: "var(--bg-glass)",
    border: "1px solid var(--border-color)",
    color: "var(--text-muted)",
    fontSize: 10,
    padding: "2px 7px",
    borderRadius: 5,
    fontFamily: "var(--font-mono)",
  },
  tagMore: {
    fontSize: 10,
    color: "var(--text-muted)",
    fontWeight: 600,
  },
  inspectBtn: {
    padding: "6px 12px",
    fontSize: 12,
    gap: 4,
    borderRadius: 7,
  },
  emptyState: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "72px 40px",
    gap: 12,
  },
  emptyIcon: {
    width: 56, height: 56,
    borderRadius: "50%",
    background: "var(--bg-glass)",
    border: "1px solid var(--border-color)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: 600,
    color: "var(--text-secondary)",
  },
  emptyDesc: {
    fontSize: 13,
    color: "var(--text-muted)",
    textAlign: "center",
    maxWidth: 340,
    lineHeight: 1.6,
  },
  tableFooter: {
    padding: "12px 24px",
    borderTop: "1px solid var(--border-color)",
    fontSize: 12,
    color: "var(--text-muted)",
    display: "flex",
    justifyContent: "flex-end",
    background: "rgba(0,0,0,0.15)",
  },
};
