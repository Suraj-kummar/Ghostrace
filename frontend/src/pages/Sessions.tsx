import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { 
  Search, Database, DollarSign, Clock, AlertCircle, 
  ChevronRight, RefreshCw, BarChart2, Tag 
} from "lucide-react";

interface SessionsProps {
  projectId: string;
}

export function Sessions({ projectId }: SessionsProps) {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all"); // all, error, success

  const fetchSessions = async () => {
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
  };

  useEffect(() => {
    fetchSessions();
  }, [projectId]);

  // Calculations for summary metrics
  let totalCost = 0;
  let totalTokens = 0;
  let totalLatency = 0;
  let latencyCount = 0;
  let errorCount = 0;

  sessions.forEach((s) => {
    let sessionHasError = false;
    s.events?.forEach((e: any) => {
      if (e.event_type === "error" || e.error_type) {
        sessionHasError = true;
      }
      if (e.cost_usd) totalCost += e.cost_usd;
      if (e.tokens_in) totalTokens += e.tokens_in;
      if (e.tokens_out) totalTokens += e.tokens_out;
      if (e.latency_ms) {
        totalLatency += e.latency_ms;
        latencyCount++;
      }
    });
    if (sessionHasError) {
      errorCount++;
    }
  });

  const avgLatency = latencyCount > 0 ? Math.round(totalLatency / latencyCount) : 0;

  // Filter sessions
  const filteredSessions = sessions.filter((s) => {
    // 1. Search term check
    const matchesSearch = 
      s.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.name && s.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      Object.keys(s.tags).some(
        (key) => 
          key.toLowerCase().includes(searchTerm.toLowerCase()) || 
          s.tags[key].toLowerCase().includes(searchTerm.toLowerCase())
      );

    if (!matchesSearch) return false;

    // 2. Error/Success check
    const sessionHasError = s.events?.some((e: any) => e.event_type === "error" || e.error_type);
    if (filterType === "error") return sessionHasError;
    if (filterType === "success") return !sessionHasError;
    return true;
  });

  const formatTokens = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}m`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
    return num.toString();
  };

  const formatCost = (num: number) => {
    if (num === 0) return "$0.00";
    if (num < 0.01) return `$${num.toFixed(4)}`;
    return `$${num.toFixed(2)}`;
  };

  const formatLatency = (ms: number) => {
    if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
    return `${ms}ms`;
  };

  return (
    <div style={styles.container} className="animated-fade-in">
      <div style={styles.header}>
        <div>
          <h1 style={styles.pageTitle}>Sessions Explorer</h1>
          <p style={styles.pageSubtitle}>Monitor runs, view latencies, error states, and token cost details.</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchSessions} disabled={loading} style={styles.refreshBtn}>
          <RefreshCw size={14} className={loading ? "spin" : ""} style={styles.refreshIcon} />
          Refresh
        </button>
      </div>

      {/* Metrics Banner */}
      <div style={styles.metricsGrid}>
        <div className="card" style={styles.metricCard}>
          <div style={styles.metricHeader}>
            <BarChart2 size={16} style={{ color: "var(--color-primary)" }} />
            <span style={styles.metricLabel}>Total Sessions</span>
          </div>
          <span style={styles.metricValue}>{sessions.length}</span>
          <span style={styles.metricSub}>{errorCount} errored runs</span>
        </div>

        <div className="card" style={styles.metricCard}>
          <div style={styles.metricHeader}>
            <DollarSign size={16} style={{ color: "var(--color-success)" }} />
            <span style={styles.metricLabel}>Aggregated Cost</span>
          </div>
          <span style={styles.metricValue}>{formatCost(totalCost)}</span>
          <span style={styles.metricSub}>All models included</span>
        </div>

        <div className="card" style={styles.metricCard}>
          <div style={styles.metricHeader}>
            <Database size={16} style={{ color: "var(--color-info)" }} />
            <span style={styles.metricLabel}>Total Tokens</span>
          </div>
          <span style={styles.metricValue}>{formatTokens(totalTokens)}</span>
          <span style={styles.metricSub}>Prompt + Output</span>
        </div>

        <div className="card" style={styles.metricCard}>
          <div style={styles.metricHeader}>
            <Clock size={16} style={{ color: "var(--color-warning)" }} />
            <span style={styles.metricLabel}>Average Latency</span>
          </div>
          <span style={styles.metricValue}>{formatLatency(avgLatency)}</span>
          <span style={styles.metricSub}>Per trace execution</span>
        </div>
      </div>

      {/* Filters bar */}
      <div style={styles.filtersBar}>
        <div style={styles.searchWrapper}>
          <Search size={16} style={styles.searchIcon} />
          <input
            className="input-field"
            type="text"
            placeholder="Search by session name, ID, or tags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={styles.searchInput}
          />
        </div>

        <div style={styles.filterGroup}>
          <button
            style={{
              ...styles.filterBtn,
              backgroundColor: filterType === "all" ? "var(--bg-surface-hover)" : "transparent",
              color: filterType === "all" ? "var(--text-primary)" : "var(--text-secondary)",
            }}
            onClick={() => setFilterType("all")}
          >
            All Runs
          </button>
          <button
            style={{
              ...styles.filterBtn,
              backgroundColor: filterType === "success" ? "var(--bg-surface-hover)" : "transparent",
              color: filterType === "success" ? "var(--text-primary)" : "var(--text-secondary)",
            }}
            onClick={() => setFilterType("success")}
          >
            Success
          </button>
          <button
            style={{
              ...styles.filterBtn,
              backgroundColor: filterType === "error" ? "var(--bg-surface-hover)" : "transparent",
              color: filterType === "error" ? "var(--text-primary)" : "var(--text-secondary)",
            }}
            onClick={() => setFilterType("error")}
          >
            Errors
          </button>
        </div>
      </div>

      {/* Sessions list */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.tableHeaderRow}>
              <th style={styles.th}>Session Name / ID</th>
              <th style={styles.th}>Status</th>
              <th style={styles.th}>Tags</th>
              <th style={styles.th}>Events</th>
              <th style={styles.th}>Tokens</th>
              <th style={styles.th}>Cost</th>
              <th style={styles.th}>Duration</th>
              <th style={{ ...styles.th, textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={styles.tableFeedback}>
                  Loading sessions...
                </td>
              </tr>
            ) : filteredSessions.length === 0 ? (
              <tr>
                <td colSpan={8} style={styles.tableFeedback}>
                  No tracing sessions found. Ensure the SDK is configured correctly.
                </td>
              </tr>
            ) : (
              filteredSessions.map((session) => {
                const sessionHasError = session.events?.some(
                  (e: any) => e.event_type === "error" || e.error_type
                );
                
                // Accumulators
                let sessionCost = 0;
                let sessionTokens = 0;
                let sessionLatency = 0;
                let sessionLatencyCount = 0;

                session.events?.forEach((e: any) => {
                  if (e.cost_usd) sessionCost += e.cost_usd;
                  if (e.tokens_in) sessionTokens += e.tokens_in;
                  if (e.tokens_out) sessionTokens += e.tokens_out;
                  if (e.latency_ms) {
                    sessionLatency += e.latency_ms;
                    sessionLatencyCount++;
                  }
                });

                return (
                  <tr key={session.id} style={styles.tr}>
                    <td style={styles.td}>
                      <Link to={`/sessions/${session.id}`} style={styles.sessionLink}>
                        <span style={styles.sessionName}>
                          {session.name || "Unnamed Session"}
                        </span>
                        <code style={styles.sessionId}>{session.id.substring(0, 18)}...</code>
                      </Link>
                    </td>
                    <td style={styles.td}>
                      {sessionHasError ? (
                        <span className="badge badge-error" style={styles.statusBadge}>
                          <AlertCircle size={12} style={{ marginRight: 4 }} />
                          Error
                        </span>
                      ) : (
                        <span className="badge badge-success" style={styles.statusBadge}>
                          Success
                        </span>
                      )}
                    </td>
                    <td style={styles.td}>
                      <div style={styles.tagsContainer}>
                        {Object.entries(session.tags).slice(0, 3).map(([k, v]) => (
                          <span key={k} style={styles.tagBadge}>
                            <Tag size={10} style={{ marginRight: 3, opacity: 0.7 }} />
                            {k}:{String(v)}
                          </span>
                        ))}
                        {Object.keys(session.tags).length > 3 && (
                          <span style={styles.tagMore}>+{Object.keys(session.tags).length - 3}</span>
                        )}
                      </div>
                    </td>
                    <td style={styles.td}>{session.events?.length || 0}</td>
                    <td style={styles.td}>{formatTokens(sessionTokens)}</td>
                    <td style={styles.td}>{formatCost(sessionCost)}</td>
                    <td style={styles.td}>{formatLatency(sessionLatency)}</td>
                    <td style={{ ...styles.td, textAlign: "right" }}>
                      <Link to={`/sessions/${session.id}`} className="btn btn-secondary" style={styles.inspectBtn}>
                        Inspect
                        <ChevronRight size={14} />
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
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
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "32px",
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
  },
  refreshBtn: {
    gap: "6px",
    padding: "8px 14px",
    fontSize: "13px",
  },
  refreshIcon: {
    transition: "transform 0.5s ease",
  },
  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "20px",
    marginBottom: "32px",
  },
  metricCard: {
    display: "flex",
    flexDirection: "column",
    padding: "20px",
  },
  metricHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "12px",
  },
  metricLabel: {
    fontSize: "12px",
    fontWeight: 500,
    color: "var(--text-secondary)",
    fontFamily: "var(--font-heading)",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  metricValue: {
    fontFamily: "var(--font-heading)",
    fontSize: "28px",
    fontWeight: 700,
    color: "var(--text-primary)",
    marginBottom: "4px",
    lineHeight: 1.1,
  },
  metricSub: {
    fontSize: "11px",
    color: "var(--text-muted)",
  },
  filtersBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "24px",
    marginBottom: "20px",
  },
  searchWrapper: {
    position: "relative",
    flex: 1,
    maxWidth: "480px",
    display: "flex",
    alignItems: "center",
  },
  searchIcon: {
    position: "absolute",
    left: "14px",
    color: "var(--text-muted)",
    pointerEvents: "none",
  },
  searchInput: {
    paddingLeft: "42px",
    width: "100%",
    fontSize: "14px",
  },
  filterGroup: {
    display: "flex",
    backgroundColor: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    borderRadius: "8px",
    padding: "4px",
  },
  filterBtn: {
    padding: "6px 14px",
    fontSize: "13px",
    fontWeight: 500,
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    transition: "all 0.15s",
    outline: "none",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    textAlign: "left",
    fontSize: "14px",
  },
  tableHeaderRow: {
    borderBottom: "1px solid var(--border-color)",
    backgroundColor: "rgba(18, 18, 20, 0.4)",
  },
  th: {
    padding: "16px 24px",
    fontWeight: 600,
    color: "var(--text-secondary)",
    fontSize: "13px",
  },
  tr: {
    borderBottom: "1px solid var(--border-color)",
    transition: "background-color 0.15s",
  },
  td: {
    padding: "16px 24px",
    verticalAlign: "middle",
    color: "var(--text-primary)",
  },
  sessionLink: {
    display: "flex",
    flexDirection: "column",
    textDecoration: "none",
    gap: "4px",
  },
  sessionName: {
    fontWeight: 600,
    color: "var(--text-primary)",
  },
  sessionId: {
    fontSize: "11px",
    color: "var(--text-muted)",
  },
  statusBadge: {
    gap: "4px",
  },
  tagsContainer: {
    display: "flex",
    flexWrap: "wrap",
    gap: "6px",
  },
  tagBadge: {
    display: "inline-flex",
    alignItems: "center",
    backgroundColor: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    color: "var(--text-secondary)",
    fontSize: "11px",
    padding: "2px 8px",
    borderRadius: "4px",
  },
  tagMore: {
    fontSize: "10px",
    color: "var(--text-muted)",
    alignSelf: "center",
  },
  inspectBtn: {
    padding: "6px 12px",
    fontSize: "12px",
    gap: "4px",
  },
  tableFeedback: {
    textAlign: "center",
    padding: "60px 0",
    color: "var(--text-muted)",
  },
};
