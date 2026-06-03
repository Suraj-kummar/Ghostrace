import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../services/api";
import {
  ArrowLeft, MessageSquare, Wrench, AlertTriangle,
  Settings, Clock, Coins, DollarSign, Tag, Cpu,
  ChevronRight, Copy, Check, Zap
} from "lucide-react";

export function SessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const fetchSessionDetail = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await api.getSessionDetail(sessionId);
      setSession(data);
      if (data.events?.length > 0) setSelectedEventId(data.events[0].id);
    } catch (err) {
      console.error("Error fetching session detail", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSessionDetail(); }, [sessionId]);

  const copyId = () => {
    navigator.clipboard.writeText(sessionId || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div style={styles.loadingState}>
        <div style={styles.loadingSpinner} />
        <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 16 }}>
          Loading trace data…
        </p>
      </div>
    );
  }

  if (!session) {
    return (
      <div style={styles.errorState} className="animated-fade-in">
        <div style={styles.errorIcon}>
          <AlertTriangle size={28} style={{ color: "var(--color-error)" }} />
        </div>
        <h2 style={styles.errorTitle}>Session not found</h2>
        <p style={styles.errorDesc}>
          Could not retrieve trace data for session ID{" "}
          <code style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
            {sessionId}
          </code>
        </p>
        <Link to="/" className="btn btn-secondary" style={{ marginTop: 20, gap: 8 }}>
          <ArrowLeft size={15} /> Back to Sessions
        </Link>
      </div>
    );
  }

  let totalCost = 0, totalTokens = 0, totalLatency = 0, hasError = false;
  session.events?.forEach((e: any) => {
    if (e.event_type === "error" || e.error_type) hasError = true;
    if (e.cost_usd) totalCost += e.cost_usd;
    if (e.tokens_in) totalTokens += e.tokens_in;
    if (e.tokens_out) totalTokens += e.tokens_out;
    if (e.latency_ms) totalLatency += e.latency_ms;
  });

  const selectedEvent = session.events?.find((e: any) => e.id === selectedEventId);

  const fmt = {
    cost: (n: number) => n === 0 ? "$0.00" : n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(2)}`,
    lat: (ms: number) => ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`,
  };

  const getEventStyle = (type: string) => {
    switch (type) {
      case "llm_call":   return { color: "#a855f7", bg: "rgba(168,85,247,0.12)", label: "LLM" };
      case "tool_call":  return { color: "#38bdf8", bg: "rgba(56,189,248,0.12)", label: "Tool" };
      case "error":      return { color: "#f43f5e", bg: "rgba(244,63,94,0.12)", label: "Error" };
      default:           return { color: "#a1a1aa", bg: "rgba(161,161,170,0.1)", label: "Log" };
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case "llm_call":  return <MessageSquare size={13} />;
      case "tool_call": return <Wrench size={13} />;
      case "error":     return <AlertTriangle size={13} />;
      default:          return <Settings size={13} />;
    }
  };

  return (
    <div style={styles.container} className="animated-fade-in">
      {/* ── Top nav ── */}
      <div style={styles.topNav}>
        <Link to="/" style={styles.backBtn}>
          <ArrowLeft size={14} />
          Sessions
        </Link>
        <div style={styles.sessionIdBadge}>
          <code style={styles.sessionIdText}>{session.id}</code>
          <button style={styles.copyIdBtn} onClick={copyId} title="Copy ID">
            {copied
              ? <Check size={12} style={{ color: "var(--color-success)" }} />
              : <Copy size={12} />}
          </button>
        </div>
      </div>

      {/* ── Three-column layout ── */}
      <div style={styles.splitLayout}>

        {/* ── LEFT: Summary card ── */}
        <div style={styles.leftCol}>
          <div className="card" style={styles.summaryCard}>
            {/* Status strip */}
            <div style={{
              ...styles.statusStrip,
              background: hasError
                ? "linear-gradient(90deg, rgba(244,63,94,0.3), transparent)"
                : "linear-gradient(90deg, rgba(16,185,129,0.3), transparent)",
            }} />

            <div style={styles.sessionMeta}>
              <h2 style={styles.sessionName}>{session.name || "Unnamed Session"}</h2>
              {hasError
                ? <span className="badge badge-error" style={{ gap: 5 }}><AlertTriangle size={11} />Failed</span>
                : <span className="badge badge-success" style={{ gap: 5 }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--color-success)", display: "inline-block" }} />
                    Completed
                  </span>
              }
            </div>

            <div className="glow-divider" />

            {/* Stats grid */}
            <div style={styles.statsGrid}>
              {[
                { label: "Started", value: new Date(session.started_at).toLocaleString(), mono: false },
                { label: "Duration", value: fmt.lat(totalLatency), mono: true },
                { label: "Total Cost", value: fmt.cost(totalCost), mono: true },
                { label: "Tokens", value: totalTokens.toLocaleString(), mono: true },
                { label: "Events", value: String(session.events?.length || 0), mono: true },
              ].map((s, i) => (
                <div key={i} style={styles.statRow}>
                  <span style={styles.statLabel}>{s.label}</span>
                  <span style={s.mono ? styles.statMono : styles.statVal}>{s.value}</span>
                </div>
              ))}
            </div>

            <div className="glow-divider" />

            {/* Tags */}
            <p style={styles.sectionLabel}>Tags</p>
            <div style={styles.tagsWrap}>
              {Object.keys(session.tags ?? {}).length === 0 ? (
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>No tags</span>
              ) : (
                Object.entries(session.tags ?? {}).map(([k, v]) => (
                  <span key={k} style={styles.tagChip}>
                    <Tag size={9} />
                    {k}: {String(v)}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        {/* ── CENTER: Timeline ── */}
        <div style={styles.centerCol}>
          <div style={styles.timelineHeader}>
            <p style={styles.sectionLabel}>Execution Timeline</p>
            <span style={styles.eventCount}>{session.events?.length || 0} events</span>
          </div>

          <div style={styles.timelineWrap}>
            {/* Vertical line */}
            <div style={styles.timelineLine} />

            {session.events?.length === 0 ? (
              <div style={styles.noEvents}>
                <Zap size={24} style={{ color: "var(--text-muted)" }} />
                <p>No trace events captured</p>
              </div>
            ) : (
              session.events?.map((ev: any, idx: number) => {
                const evStyle = getEventStyle(ev.event_type);
                const isSelected = ev.id === selectedEventId;
                const isError = ev.event_type === "error" || ev.error_type;

                return (
                  <div
                    key={ev.id}
                    style={styles.timelineNode}
                    className="animated-fade-in"
                  >
                    {/* Dot marker */}
                    <div style={{
                      ...styles.timelineDot,
                      background: isSelected ? evStyle.color : "var(--bg-surface)",
                      border: `2px solid ${isSelected ? evStyle.color : isError ? "var(--color-error)" : "var(--border-color-hover)"}`,
                      boxShadow: isSelected ? `0 0 12px ${evStyle.color}66` : "none",
                    }}>
                      <span style={{ color: isSelected ? "white" : evStyle.color }}>
                        {getEventIcon(ev.event_type)}
                      </span>
                    </div>

                    {/* Event card */}
                    <div
                      className="card"
                      style={{
                        ...styles.eventCard,
                        borderColor: isSelected ? `${evStyle.color}55` : "var(--border-color)",
                        background: isSelected
                          ? `${evStyle.bg}`
                          : "var(--bg-card)",
                        cursor: "pointer",
                        transform: isSelected ? "translateX(2px)" : "none",
                      }}
                      onClick={() => setSelectedEventId(ev.id)}
                    >
                      <div style={styles.eventCardTop}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={styles.eventSeq}>#{ev.sequence_number}</span>
                          <span style={{
                            ...styles.eventTypePill,
                            background: evStyle.bg,
                            color: evStyle.color,
                          }}>
                            {evStyle.label}
                          </span>
                        </div>
                        <div style={styles.eventMetrics}>
                          {ev.latency_ms && (
                            <span style={styles.metricChip}>
                              <Clock size={9} /> {fmt.lat(ev.latency_ms)}
                            </span>
                          )}
                          {ev.cost_usd ? (
                            <span style={styles.metricChip}>
                              <DollarSign size={9} /> {fmt.cost(ev.cost_usd)}
                            </span>
                          ) : null}
                        </div>
                      </div>
                      <span style={styles.eventSummaryText}>
                        {ev.event_type === "llm_call" && (ev.model || "LLM Call")}
                        {ev.event_type === "tool_call" && (ev.tool_name ? `tool: ${ev.tool_name}` : "Tool Execution")}
                        {ev.event_type === "error" && (ev.error_type || "Exception raised")}
                        {ev.event_type === "custom" && "Custom trace log"}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* ── RIGHT: Inspector ── */}
        <div style={styles.rightCol}>
          <div className="card" style={styles.inspectorCard}>
            <div style={styles.inspectorTitleRow}>
              <h3 style={styles.inspectorTitle}>Trace Inspector</h3>
              {selectedEvent && (
                <span style={{
                  ...styles.eventTypePill,
                  background: getEventStyle(selectedEvent.event_type).bg,
                  color: getEventStyle(selectedEvent.event_type).color,
                  fontSize: 11,
                }}>
                  {getEventStyle(selectedEvent.event_type).label}
                </span>
              )}
            </div>

            {selectedEvent ? (
              <div style={styles.inspectorBody} className="animated-fade-in" key={selectedEvent.id}>
                {/* Meta banner */}
                <div style={styles.metaBanner}>
                  {[
                    ["Type", selectedEvent.event_type.replace("_", " ").toUpperCase()],
                    ["Timestamp", new Date(selectedEvent.timestamp).toLocaleTimeString()],
                    ...(selectedEvent.latency_ms ? [["Latency", fmt.lat(selectedEvent.latency_ms)]] : []),
                  ].map(([l, v]) => (
                    <div key={l} style={styles.metaRow}>
                      <span style={styles.metaLabel}>{l}</span>
                      <span style={styles.metaVal}>{v}</span>
                    </div>
                  ))}
                </div>

                {/* LLM Call */}
                {selectedEvent.event_type === "llm_call" && (
                  <div style={styles.inspectorSection}>
                    <div style={styles.modelRow}>
                      <span style={styles.inspLabel}>Model</span>
                      <span className="badge badge-info" style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>
                        {selectedEvent.model || "unknown"}
                      </span>
                    </div>
                    <div style={styles.tokenGrid}>
                      {[
                        { icon: <Coins size={14} />, color: "var(--color-info)", num: selectedEvent.tokens_in?.toLocaleString() || 0, lbl: "Input tokens" },
                        { icon: <Cpu size={14} />, color: "var(--color-success)", num: selectedEvent.tokens_out?.toLocaleString() || 0, lbl: "Output tokens" },
                      ].map((t, i) => (
                        <div key={i} style={styles.tokenCard}>
                          <span style={{ color: t.color }}>{t.icon}</span>
                          <div>
                            <div style={styles.tokenNum}>{t.num}</div>
                            <div style={styles.tokenLbl}>{t.lbl}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <CodeBlock title="Prompt payload" content={selectedEvent.prompt || "No prompt recorded."} />
                    <CodeBlock title="Model response" content={selectedEvent.response || "No response recorded."} />
                  </div>
                )}

                {/* Tool call */}
                {selectedEvent.event_type === "tool_call" && (
                  <div style={styles.inspectorSection}>
                    <div style={styles.modelRow}>
                      <span style={styles.inspLabel}>Tool</span>
                      <span className="badge badge-info" style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>
                        {selectedEvent.tool_name || "unknown_tool"}
                      </span>
                    </div>
                    <CodeBlock
                      title="Arguments (JSON)"
                      content={selectedEvent.tool_input ? JSON.stringify(selectedEvent.tool_input, null, 2) : "No arguments recorded."}
                    />
                    <CodeBlock
                      title="Output"
                      content={typeof selectedEvent.tool_output === "object"
                        ? JSON.stringify(selectedEvent.tool_output, null, 2)
                        : String(selectedEvent.tool_output || "No output recorded.")}
                    />
                  </div>
                )}

                {/* Error */}
                {selectedEvent.event_type === "error" && (
                  <div style={styles.inspectorSection}>
                    <div style={styles.errorBanner}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <AlertTriangle size={16} style={{ color: "var(--color-error)", flexShrink: 0 }} />
                        <span style={styles.errorClass}>{selectedEvent.error_type || "RuntimeError"}</span>
                      </div>
                      <p style={styles.errorMsg}>{selectedEvent.error_message || "An exception was raised."}</p>
                    </div>
                    <CodeBlock
                      title="Stack trace"
                      content={selectedEvent.stack_trace || "No traceback available."}
                      isError
                    />
                  </div>
                )}

                {/* Metadata */}
                {selectedEvent.metadata && Object.keys(selectedEvent.metadata).length > 0 && (
                  <CodeBlock
                    title="Extra metadata"
                    content={JSON.stringify(selectedEvent.metadata, null, 2)}
                  />
                )}
              </div>
            ) : (
              <div style={styles.emptyInspector}>
                <div style={styles.emptyInspectorIcon}>
                  <ChevronRight size={20} style={{ color: "var(--text-muted)" }} />
                </div>
                <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 10 }}>
                  Select an event from the timeline
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* Reusable code block sub-component */
function CodeBlock({ title, content, isError = false }: { title: string; content: string; isError?: boolean }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={cbStyles.title}>{title}</span>
        <button style={cbStyles.copyBtn} onClick={copy}>
          {copied ? <Check size={11} style={{ color: "var(--color-success)" }} /> : <Copy size={11} />}
        </button>
      </div>
      <pre style={{
        ...cbStyles.pre,
        borderLeftColor: isError ? "var(--color-error)" : "var(--color-primary)",
        color: isError ? "var(--color-error)" : "#c4c4d4",
      }}>
        {content}
      </pre>
    </div>
  );
}

const cbStyles: Record<string, React.CSSProperties> = {
  title: { fontSize: 11, fontWeight: 600, color: "var(--text-muted)", fontFamily: "var(--font-heading)", letterSpacing: "0.3px" },
  copyBtn: {
    background: "none", border: "none", cursor: "pointer",
    color: "var(--text-muted)", padding: 4, borderRadius: 4,
    display: "flex", alignItems: "center",
  },
  pre: {
    background: "rgba(0,0,0,0.45)",
    border: "1px solid var(--border-color)",
    borderLeft: "3px solid var(--color-primary)",
    borderRadius: "0 8px 8px 0",
    padding: "12px 14px",
    fontFamily: "var(--font-mono)",
    fontSize: 12,
    overflowX: "auto",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
    lineHeight: 1.6,
    maxHeight: 240,
    overflowY: "auto",
  },
};

const styles: Record<string, React.CSSProperties> = {
  container: { padding: "28px 32px", display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden", gap: 20 },
  topNav: { display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 },
  backBtn: {
    display: "flex", alignItems: "center", gap: 7,
    color: "var(--text-secondary)", textDecoration: "none",
    fontSize: 13, fontWeight: 600,
    background: "var(--bg-glass)", border: "1px solid var(--border-color)",
    borderRadius: 8, padding: "7px 14px",
    transition: "all 0.2s",
  },
  sessionIdBadge: {
    display: "flex", alignItems: "center", gap: 8,
    background: "var(--bg-glass)", border: "1px solid var(--border-color)",
    borderRadius: 8, padding: "6px 12px",
  },
  sessionIdText: { fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono)" },
  copyIdBtn: {
    background: "none", border: "none", cursor: "pointer",
    color: "var(--text-muted)", display: "flex", alignItems: "center",
    padding: 2, borderRadius: 4,
  },

  splitLayout: { display: "grid", gridTemplateColumns: "280px 1fr 420px", gap: 20, flex: 1, overflow: "hidden" },

  leftCol: { display: "flex", flexDirection: "column", overflowY: "auto" },
  centerCol: { display: "flex", flexDirection: "column", overflowY: "auto" },
  rightCol: { display: "flex", flexDirection: "column", overflow: "hidden" },

  summaryCard: { padding: "22px", position: "relative", overflow: "hidden" },
  statusStrip: { position: "absolute", top: 0, left: 0, right: 0, height: 3 },
  sessionMeta: { display: "flex", flexDirection: "column", gap: 10, marginBottom: 14 },
  sessionName: { fontFamily: "var(--font-heading)", fontSize: 18, fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.3 },

  statsGrid: { display: "flex", flexDirection: "column", gap: 10 },
  statRow: { display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 13 },
  statLabel: { color: "var(--text-secondary)", fontWeight: 500 },
  statVal: { fontWeight: 600, color: "var(--text-primary)" },
  statMono: { fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--text-primary)", fontSize: 12 },

  sectionLabel: { fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: 8 },
  tagsWrap: { display: "flex", flexWrap: "wrap", gap: 6 },
  tagChip: {
    display: "inline-flex", alignItems: "center", gap: 5,
    background: "var(--bg-glass)", border: "1px solid var(--border-color)",
    color: "var(--text-muted)", fontSize: 10, padding: "3px 8px", borderRadius: 5,
    fontFamily: "var(--font-mono)",
  },

  timelineHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexShrink: 0 },
  eventCount: { fontSize: 12, color: "var(--text-muted)", fontWeight: 600, background: "var(--bg-glass)", border: "1px solid var(--border-color)", borderRadius: 99, padding: "2px 10px" },

  timelineWrap: { position: "relative", paddingLeft: 28, display: "flex", flexDirection: "column", gap: 12 },
  timelineLine: {
    position: "absolute", left: 11, top: 8, bottom: 8, width: 2,
    background: "linear-gradient(180deg, var(--color-primary) 0%, rgba(99,102,241,0.2) 80%, transparent 100%)",
    borderRadius: 2,
    zIndex: 1,
  },
  timelineNode: { position: "relative", display: "flex", gap: 14, alignItems: "flex-start" },
  timelineDot: {
    position: "absolute", left: -28, top: 14,
    width: 24, height: 24, borderRadius: "50%",
    display: "flex", alignItems: "center", justifyContent: "center",
    zIndex: 5, transition: "all 0.2s", flexShrink: 0,
  },
  eventCard: { flex: 1, padding: "14px 16px", display: "flex", flexDirection: "column", gap: 6, transition: "all 0.15s" },
  eventCardTop: { display: "flex", alignItems: "center", justifyContent: "space-between" },
  eventSeq: { fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-muted)" },
  eventTypePill: { fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 99, letterSpacing: "0.3px" },
  eventMetrics: { display: "flex", gap: 6 },
  metricChip: { display: "inline-flex", alignItems: "center", gap: 4, fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono)" },
  eventSummaryText: { fontSize: 13, fontWeight: 600, color: "var(--text-primary)" },

  inspectorCard: { display: "flex", flexDirection: "column", height: "100%", padding: 22, overflow: "hidden" },
  inspectorTitleRow: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16, flexShrink: 0 },
  inspectorTitle: { fontFamily: "var(--font-heading)", fontSize: 16, fontWeight: 700, color: "var(--text-primary)" },
  inspectorBody: { display: "flex", flexDirection: "column", gap: 16, overflowY: "auto", flex: 1, paddingRight: 2 },

  metaBanner: {
    background: "var(--bg-glass)", border: "1px solid var(--border-color)",
    borderRadius: 10, padding: "12px 16px", display: "flex", flexDirection: "column", gap: 8,
  },
  metaRow: { display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 12 },
  metaLabel: { color: "var(--text-secondary)", fontWeight: 500 },
  metaVal: { fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-mono)", fontSize: 11 },

  inspectorSection: { display: "flex", flexDirection: "column", gap: 14 },
  modelRow: { display: "flex", alignItems: "center", justifyContent: "space-between" },
  inspLabel: { fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" },

  tokenGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 },
  tokenCard: {
    background: "var(--bg-glass)", border: "1px solid var(--border-color)",
    borderRadius: 10, padding: "12px", display: "flex", alignItems: "center", gap: 10,
  },
  tokenNum: { fontSize: 16, fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-mono)" },
  tokenLbl: { fontSize: 10, color: "var(--text-muted)", marginTop: 2 },

  errorBanner: {
    background: "rgba(244,63,94,0.05)", border: "1px solid rgba(244,63,94,0.2)",
    borderRadius: 10, padding: 16, display: "flex", flexDirection: "column", gap: 8,
  },
  errorClass: { fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 700, color: "var(--color-error)" },
  errorMsg: { fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5 },

  emptyInspector: { flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" },
  emptyInspectorIcon: {
    width: 44, height: 44, borderRadius: "50%",
    background: "var(--bg-glass)", border: "1px solid var(--border-color)",
    display: "flex", alignItems: "center", justifyContent: "center",
  },

  noEvents: { display: "flex", flexDirection: "column", alignItems: "center", gap: 10, padding: "40px 0", color: "var(--text-muted)", fontSize: 14 },

  loadingState: { display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, minHeight: "60vh" },
  loadingSpinner: {
    width: 36, height: 36, borderRadius: "50%",
    border: "3px solid var(--border-color)",
    borderTopColor: "var(--color-primary)",
    animation: "spin 0.7s linear infinite",
  },
  errorState: { display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, padding: 60, gap: 12 },
  errorIcon: {
    width: 64, height: 64, borderRadius: "50%",
    background: "rgba(244,63,94,0.08)", border: "1px solid rgba(244,63,94,0.2)",
    display: "flex", alignItems: "center", justifyContent: "center",
    marginBottom: 8,
  },
  errorTitle: { fontFamily: "var(--font-heading)", fontSize: 20, fontWeight: 700, color: "var(--text-primary)" },
  errorDesc: { fontSize: 14, color: "var(--text-secondary)", textAlign: "center", lineHeight: 1.6 },
};
