import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../services/api";
import { 
  ArrowLeft, MessageSquare, Wrench, AlertTriangle, 
  Settings, Clock, Coins, DollarSign, Tag, Cpu 
} from "lucide-react";

export function SessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const fetchSessionDetail = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const data = await api.getSessionDetail(sessionId);
      setSession(data);
      if (data.events && data.events.length > 0) {
        // Auto-select the first event
        setSelectedEventId(data.events[0].id);
      }
    } catch (err) {
      console.error("Error fetching session detail", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionDetail();
  }, [sessionId]);

  if (loading) {
    return <div style={styles.loading}>Loading session details...</div>;
  }

  if (!session) {
    return (
      <div style={styles.errorContainer}>
        <AlertTriangle size={48} style={{ color: "var(--color-error)", marginBottom: 16 }} />
        <h2>Session Not Found</h2>
        <p>Could not retrieve trace logs for session ID "{sessionId}".</p>
        <Link to="/" className="btn btn-secondary" style={{ marginTop: 20 }}>
          <ArrowLeft size={16} /> Back to Sessions
        </Link>
      </div>
    );
  }

  // Calculate session summary stats
  let totalCost = 0;
  let totalTokens = 0;
  let totalLatency = 0;
  let hasError = false;

  session.events?.forEach((e: any) => {
    if (e.event_type === "error" || e.error_type) hasError = true;
    if (e.cost_usd) totalCost += e.cost_usd;
    if (e.tokens_in) totalTokens += e.tokens_in;
    if (e.tokens_out) totalTokens += e.tokens_out;
    if (e.latency_ms) totalLatency += e.latency_ms;
  });

  const selectedEvent = session.events?.find((e: any) => e.id === selectedEventId);

  const formatCost = (num: number) => {
    if (num === 0) return "$0.00";
    if (num < 0.01) return `$${num.toFixed(4)}`;
    return `$${num.toFixed(2)}`;
  };

  const formatLatency = (ms: number) => {
    if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
    return `${ms}ms`;
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case "llm_call":
        return <MessageSquare size={14} style={{ color: "#a855f7" }} />;
      case "tool_call":
        return <Wrench size={14} style={{ color: "#0ea5e9" }} />;
      case "error":
        return <AlertTriangle size={14} style={{ color: "#ef4444" }} />;
      default:
        return <Settings size={14} style={{ color: "#a1a1aa" }} />;
    }
  };

  return (
    <div style={styles.container} className="animated-fade-in">
      {/* Top back nav */}
      <div style={styles.topNav}>
        <Link to="/" style={styles.backLink}>
          <ArrowLeft size={16} />
          Back to Sessions
        </Link>
        <span style={styles.topSessionId}>Session ID: {session.id}</span>
      </div>

      <div style={styles.splitLayout}>
        {/* Left summary card */}
        <div style={styles.leftCol}>
          <div className="card" style={styles.summaryCard}>
            <div style={styles.summaryHeader}>
              <h2 style={styles.sessionName}>{session.name || "Unnamed Session"}</h2>
              {hasError ? (
                <span className="badge badge-error">Failed</span>
              ) : (
                <span className="badge badge-success">Completed</span>
              )}
            </div>

            <div style={styles.divider}></div>

            <div style={styles.metaList}>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Started</span>
                <span style={styles.metaVal}>
                  {new Date(session.started_at).toLocaleString()}
                </span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Duration</span>
                <span style={styles.metaVal}>{formatLatency(totalLatency)}</span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Total Cost</span>
                <span style={styles.metaVal}>{formatCost(totalCost)}</span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Total Tokens</span>
                <span style={styles.metaVal}>{totalTokens.toLocaleString()}</span>
              </div>
            </div>

            <div style={styles.divider}></div>

            <h3 style={styles.sectionHeading}>Tags</h3>
            <div style={styles.tagsContainer}>
              {Object.keys(session.tags).length === 0 ? (
                <span style={styles.noTags}>No tags present</span>
              ) : (
                Object.entries(session.tags).map(([k, v]) => (
                  <span key={k} style={styles.tagBadge}>
                    <Tag size={10} style={{ marginRight: 4, opacity: 0.7 }} />
                    {k}: {String(v)}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Center timeline */}
        <div style={styles.centerCol}>
          <h3 style={styles.sectionHeading}>Execution Timeline</h3>
          <div style={styles.timelineContainer}>
            <div style={styles.timelineLine}></div>

            {session.events?.length === 0 ? (
              <div style={styles.noEvents}>No trace events captured for this session.</div>
            ) : (
              session.events?.map((e: any) => {
                const isSelected = e.id === selectedEventId;
                const isError = e.event_type === "error" || e.error_type;
                
                return (
                  <div key={e.id} style={styles.timelineNode}>
                    {/* Circle icon marker */}
                    <div 
                      style={{
                        ...styles.timelineMarker,
                        borderColor: isSelected ? "var(--color-primary)" : isError ? "var(--color-error)" : "var(--border-color)",
                        backgroundColor: isSelected ? "var(--color-primary-glow)" : "var(--bg-surface)",
                      }}
                    >
                      {getEventIcon(e.event_type)}
                    </div>

                    {/* Timeline Event Card */}
                    <div 
                      className={`card ${isSelected ? 'glow-hover' : ''}`}
                      style={{
                        ...styles.eventCard,
                        borderColor: isSelected ? "var(--color-primary)" : "var(--border-color)",
                        backgroundColor: isSelected ? "rgba(99,102,241,0.04)" : "var(--bg-card)",
                      }}
                      onClick={() => setSelectedEventId(e.id)}
                    >
                      <div style={styles.eventCardHeader}>
                        <span style={styles.eventSequence}>#{e.sequence_number}</span>
                        <span 
                          style={{
                            ...styles.eventTypeBadge,
                            color: e.event_type === "llm_call" ? "#a855f7" : e.event_type === "tool_call" ? "#0ea5e9" : isError ? "var(--color-error)" : "var(--text-secondary)"
                          }}
                        >
                          {e.event_type.replace("_", " ")}
                        </span>
                        
                        <div style={styles.eventCardMetrics}>
                          {e.latency_ms && (
                            <span style={styles.cardMetric}>
                              <Clock size={10} /> {formatLatency(e.latency_ms)}
                            </span>
                          )}
                          {e.cost_usd ? (
                            <span style={styles.cardMetric}>
                              <DollarSign size={10} /> {formatCost(e.cost_usd)}
                            </span>
                          ) : null}
                        </div>
                      </div>

                      <span style={styles.eventSummary}>
                        {e.event_type === "llm_call" && (e.model || "LLM Call")}
                        {e.event_type === "tool_call" && (e.tool_name ? `tool: ${e.tool_name}` : "Tool Execution")}
                        {e.event_type === "error" && (e.error_type || "Exception raised")}
                        {e.event_type === "custom" && "Custom Log trace"}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right detailed inspector panel */}
        <div style={styles.rightCol}>
          <div className="card" style={styles.inspectorCard}>
            <h3 style={styles.inspectorTitle}>Trace Inspector</h3>
            
            {selectedEvent ? (
              <div style={styles.inspectorBody} className="animated-fade-in">
                {/* Basic info banner */}
                <div style={styles.inspectorBanner}>
                  <div style={styles.inspectorBannerRow}>
                    <span style={styles.inspectorLabel}>Type</span>
                    <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                      {selectedEvent.event_type.toUpperCase()}
                    </span>
                  </div>
                  <div style={styles.inspectorBannerRow}>
                    <span style={styles.inspectorLabel}>Timestamp</span>
                    <span style={styles.inspectorVal}>
                      {new Date(selectedEvent.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {selectedEvent.latency_ms && (
                    <div style={styles.inspectorBannerRow}>
                      <span style={styles.inspectorLabel}>Execution Latency</span>
                      <span style={styles.inspectorVal}>{formatLatency(selectedEvent.latency_ms)}</span>
                    </div>
                  )}
                </div>

                {/* Specific Event Type Views */}
                {selectedEvent.event_type === "llm_call" && (
                  <div style={styles.inspectSection}>
                    <div style={{ ...styles.inspectorBannerRow, marginBottom: 16 }}>
                      <span style={styles.inspectorLabel}>Model name</span>
                      <span className="badge badge-info" style={{ fontFamily: "var(--font-mono)" }}>
                        {selectedEvent.model || "unknown"}
                      </span>
                    </div>

                    <div style={styles.tokenCostRow}>
                      <div style={styles.tokenStat}>
                        <Coins size={14} style={{ color: "var(--color-info)" }} />
                        <div style={styles.tokenStatVal}>
                          <span style={styles.tokenStatNum}>
                            {selectedEvent.tokens_in?.toLocaleString() || 0}
                          </span>
                          <span style={styles.tokenStatLbl}>Input Tokens</span>
                        </div>
                      </div>
                      <div style={styles.tokenStat}>
                        <Cpu size={14} style={{ color: "var(--color-success)" }} />
                        <div style={styles.tokenStatVal}>
                          <span style={styles.tokenStatNum}>
                            {selectedEvent.tokens_out?.toLocaleString() || 0}
                          </span>
                          <span style={styles.tokenStatLbl}>Output Tokens</span>
                        </div>
                      </div>
                    </div>

                    <div style={styles.codeBlockWrapper}>
                      <span style={styles.codeBlockTitle}>Prompt payload</span>
                      <pre style={styles.codeBlock}>{selectedEvent.prompt || "No prompt input recorded."}</pre>
                    </div>

                    <div style={styles.codeBlockWrapper}>
                      <span style={styles.codeBlockTitle}>Model response</span>
                      <pre style={styles.codeBlock}>{selectedEvent.response || "No response output recorded."}</pre>
                    </div>
                  </div>
                )}

                {selectedEvent.event_type === "tool_call" && (
                  <div style={styles.inspectSection}>
                    <div style={{ ...styles.inspectorBannerRow, marginBottom: 16 }}>
                      <span style={styles.inspectorLabel}>Tool Function</span>
                      <span className="badge badge-info" style={{ fontFamily: "var(--font-mono)" }}>
                        {selectedEvent.tool_name || "unknown_tool"}
                      </span>
                    </div>

                    <div style={styles.codeBlockWrapper}>
                      <span style={styles.codeBlockTitle}>Inputs (JSON arguments)</span>
                      <pre style={styles.codeBlock}>
                        {selectedEvent.tool_input 
                          ? JSON.stringify(selectedEvent.tool_input, null, 2) 
                          : "No tool arguments recorded."}
                      </pre>
                    </div>

                    <div style={styles.codeBlockWrapper}>
                      <span style={styles.codeBlockTitle}>Output</span>
                      <pre style={styles.codeBlock}>
                        {typeof selectedEvent.tool_output === "object"
                          ? JSON.stringify(selectedEvent.tool_output, null, 2)
                          : String(selectedEvent.tool_output || "No output recorded.")}
                      </pre>
                    </div>
                  </div>
                )}

                {selectedEvent.event_type === "error" && (
                  <div style={styles.inspectSection}>
                    <div style={styles.errorBanner}>
                      <div style={styles.errorHeaderRow}>
                        <AlertTriangle size={18} style={{ color: "var(--color-error)" }} />
                        <span style={styles.errorClass}>{selectedEvent.error_type || "RuntimeError"}</span>
                      </div>
                      <p style={styles.errorMessage}>{selectedEvent.error_message || "An exception was raised."}</p>
                    </div>

                    <div style={styles.codeBlockWrapper}>
                      <span style={styles.codeBlockTitle}>Stack Trace</span>
                      <pre style={{ ...styles.codeBlock, color: "var(--color-error)", borderLeft: "3px solid var(--color-error)" }}>
                        {selectedEvent.stack_trace || "No python traceback available."}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Metadata block for all events */}
                {selectedEvent.metadata && Object.keys(selectedEvent.metadata).length > 0 && (
                  <div style={styles.codeBlockWrapper}>
                    <span style={styles.codeBlockTitle}>Extensible Metadata</span>
                    <pre style={styles.codeBlock}>
                      {JSON.stringify(selectedEvent.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div style={styles.emptyInspector}>Select an event from the timeline to inspect details.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: "32px",
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    overflow: "hidden",
  },
  topNav: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "24px",
    flexShrink: 0,
  },
  backLink: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    color: "var(--text-secondary)",
    textDecoration: "none",
    fontSize: "14px",
    fontWeight: 500,
    transition: "color 0.2s",
  },
  topSessionId: {
    fontSize: "12px",
    color: "var(--text-muted)",
    fontFamily: "var(--font-mono)",
  },
  splitLayout: {
    display: "grid",
    gridTemplateColumns: "280px 1fr 480px",
    gap: "24px",
    flex: 1,
    overflow: "hidden",
  },
  leftCol: {
    display: "flex",
    flexDirection: "column",
    overflowY: "auto",
  },
  centerCol: {
    display: "flex",
    flexDirection: "column",
    overflowY: "auto",
    paddingRight: "8px",
  },
  rightCol: {
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  summaryCard: {
    display: "flex",
    flexDirection: "column",
    height: "fit-content",
  },
  summaryHeader: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    alignItems: "start",
    marginBottom: "16px",
  },
  sessionName: {
    fontFamily: "var(--font-heading)",
    fontSize: "20px",
    fontWeight: 600,
    color: "var(--text-primary)",
    wordBreak: "break-word",
  },
  divider: {
    height: "1px",
    backgroundColor: "var(--border-color)",
    margin: "16px 0",
  },
  metaList: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  metaItem: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: "13px",
  },
  metaLabel: {
    color: "var(--text-secondary)",
  },
  metaVal: {
    fontWeight: 600,
    color: "var(--text-primary)",
  },
  sectionHeading: {
    fontFamily: "var(--font-heading)",
    fontSize: "15px",
    fontWeight: 600,
    color: "var(--text-primary)",
    marginBottom: "12px",
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
    padding: "4px 8px",
    borderRadius: "4px",
  },
  noTags: {
    fontSize: "12px",
    color: "var(--text-muted)",
  },
  timelineContainer: {
    position: "relative",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    paddingLeft: "24px",
  },
  timelineLine: {
    position: "absolute",
    left: "11px",
    top: "12px",
    bottom: "12px",
    width: "2px",
    backgroundColor: "var(--border-color)",
    zIndex: 1,
  },
  timelineNode: {
    position: "relative",
    display: "flex",
    gap: "16px",
    alignItems: "stretch",
  },
  timelineMarker: {
    position: "absolute",
    left: "-24px",
    top: "14px",
    width: "24px",
    height: "24px",
    borderRadius: "50%",
    border: "2px solid",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 5,
    transition: "all 0.2s",
  },
  eventCard: {
    flex: 1,
    padding: "16px",
    cursor: "pointer",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  eventCardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    fontSize: "12px",
  },
  eventSequence: {
    fontFamily: "var(--font-mono)",
    color: "var(--text-muted)",
  },
  eventTypeBadge: {
    fontWeight: 600,
    textTransform: "uppercase",
    fontSize: "11px",
    letterSpacing: "0.5px",
  },
  eventCardMetrics: {
    marginLeft: "auto",
    display: "flex",
    gap: "8px",
  },
  cardMetric: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    color: "var(--text-muted)",
    fontSize: "11px",
  },
  eventSummary: {
    fontWeight: 500,
    fontSize: "14px",
    color: "var(--text-primary)",
  },
  noEvents: {
    color: "var(--text-muted)",
    fontSize: "14px",
    textAlign: "center",
    padding: "40px 0",
  },
  inspectorCard: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    padding: "24px",
    overflow: "hidden",
  },
  inspectorTitle: {
    fontFamily: "var(--font-heading)",
    fontSize: "18px",
    fontWeight: 600,
    marginBottom: "16px",
    color: "var(--text-primary)",
    flexShrink: 0,
  },
  inspectorBody: {
    display: "flex",
    flexDirection: "column",
    gap: "20px",
    overflowY: "auto",
    flex: 1,
    paddingRight: "4px",
  },
  inspectorBanner: {
    backgroundColor: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    borderRadius: "8px",
    padding: "14px 16px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  inspectorBannerRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "13px",
  },
  inspectorLabel: {
    color: "var(--text-secondary)",
    fontSize: "12px",
  },
  inspectorVal: {
    fontWeight: 500,
    color: "var(--text-primary)",
  },
  inspectSection: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },
  tokenCostRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "12px",
  },
  tokenStat: {
    backgroundColor: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    borderRadius: "8px",
    padding: "10px 14px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  tokenStatVal: {
    display: "flex",
    flexDirection: "column",
  },
  tokenStatNum: {
    fontSize: "14px",
    fontWeight: 600,
    color: "var(--text-primary)",
  },
  tokenStatLbl: {
    fontSize: "10px",
    color: "var(--text-muted)",
  },
  codeBlockWrapper: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  codeBlockTitle: {
    fontSize: "12px",
    fontWeight: 500,
    color: "var(--text-secondary)",
    fontFamily: "var(--font-heading)",
  },
  codeBlock: {
    backgroundColor: "var(--bg-surface)",
    border: "1px solid var(--border-color)",
    borderRadius: "8px",
    padding: "12px 16px",
    fontFamily: "var(--font-mono)",
    fontSize: "12px",
    color: "var(--text-primary)",
    overflowX: "auto",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
    lineHeight: 1.5,
  },
  errorBanner: {
    backgroundColor: "rgba(239, 68, 68, 0.04)",
    border: "1px dashed rgba(239, 68, 68, 0.3)",
    borderRadius: "8px",
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  errorHeaderRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  errorClass: {
    fontFamily: "var(--font-mono)",
    fontSize: "13px",
    fontWeight: 600,
    color: "var(--color-error)",
  },
  errorMessage: {
    fontSize: "12px",
    color: "var(--text-secondary)",
  },
  emptyInspector: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    textAlign: "center",
    color: "var(--text-muted)",
    fontSize: "13px",
    flex: 1,
  },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "400px",
    color: "var(--text-muted)",
  },
  errorContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    padding: "80px 40px",
    textAlign: "center",
  },
};
