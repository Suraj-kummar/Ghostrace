import React, { useState, useEffect, useRef } from "react";
import { api } from "../services/api";
import {
  BarChart2, DollarSign, Database, Clock, AlertCircle,
  RefreshCw, TrendingUp, Cpu, RotateCcw, ShieldAlert,
  Activity, Zap
} from "lucide-react";

interface AnalyticsProps {
  projectId: string;
}

interface DailyMetric {
  date: string;
  sessions: number;
  events: number;
  cost_usd: number;
  tokens: number;
  errors: number;
}

interface ModelStat {
  model: string;
  calls: number;
  tokens: number;
  cost_usd: number;
}

interface AnalyticsData {
  period_days: number;
  total_sessions: number;
  total_events: number;
  total_cost_usd: number;
  total_tokens: number;
  error_sessions: number;
  loop_sessions: number;
  avg_latency_ms: number;
  avg_session_duration_ms?: number | null;
  daily: DailyMetric[];
  top_models: ModelStat[];
  error_rate_daily?: {
    date: string;
    total_sessions: number;
    error_sessions: number;
    error_rate: number;
  }[];
}

// ─── Pure-SVG chart primitives ────────────────────────────────────────────────

function AreaChart({
  data,
  color,
  height = 120,
}: {
  data: { date: string; value: number }[];
  color: string;
  height?: number;
}) {
  const width = 600;
  const pad = { top: 12, right: 8, bottom: 28, left: 36 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  const values = data.map((d) => d.value);
  const max = Math.max(...values, 1);

  const pts = data.map((d, i) => {
    const x = pad.left + (i / Math.max(data.length - 1, 1)) * innerW;
    const y = pad.top + innerH - (d.value / max) * innerH;
    return [x, y] as [number, number];
  });

  const linePath = pts
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x},${y}`)
    .join(" ");

  const areaPath =
    `${linePath} L${pts[pts.length - 1][0]},${pad.top + innerH} L${pts[0][0]},${pad.top + innerH} Z`;

  const labelStep = Math.ceil(data.length / 5);
  const chartId = `grad-${color.replace("#", "")}`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      style={{ width: "100%", height }}
    >
      <defs>
        <linearGradient id={chartId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0.01" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map((t) => {
        const y = pad.top + innerH * (1 - t);
        return (
          <g key={t}>
            <line x1={pad.left} y1={y} x2={pad.left + innerW} y2={y}
              stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
            <text x={pad.left - 6} y={y + 4} textAnchor="end"
              fontSize="9" fill="rgba(255,255,255,0.25)">
              {t === 0 ? 0 : formatCompact(max * t)}
            </text>
          </g>
        );
      })}

      {/* Area fill */}
      <path d={areaPath} fill={`url(#${chartId})`} />

      {/* Line */}
      <path d={linePath} fill="none" stroke={color} strokeWidth="1.8"
        strokeLinejoin="round" strokeLinecap="round" />

      {/* Data dots on hover-able points — just show last point */}
      {pts.length > 0 && (
        <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]}
          r="3" fill={color} />
      )}

      {/* X-axis labels */}
      {data.map((d, i) => {
        if (i % labelStep !== 0 && i !== data.length - 1) return null;
        const x = pad.left + (i / Math.max(data.length - 1, 1)) * innerW;
        const label = d.date.slice(5); // MM-DD
        return (
          <text key={i} x={x} y={pad.top + innerH + 16}
            textAnchor="middle" fontSize="9" fill="rgba(255,255,255,0.3)">
            {label}
          </text>
        );
      })}
    </svg>
  );
}

function BarChartSVG({
  data,
  color,
  height = 120,
}: {
  data: { date: string; value: number }[];
  color: string;
  height?: number;
}) {
  const width = 600;
  const pad = { top: 12, right: 8, bottom: 28, left: 36 };
  const innerW = width - pad.left - pad.right;
  const innerH = height - pad.top - pad.bottom;

  const values = data.map((d) => d.value);
  const max = Math.max(...values, 1);

  const barW = Math.max(1, innerW / data.length - 2);
  const labelStep = Math.ceil(data.length / 5);
  const chartId = `bgrad-${color.replace("#", "")}`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      style={{ width: "100%", height }}
    >
      <defs>
        <linearGradient id={chartId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.9" />
          <stop offset="100%" stopColor={color} stopOpacity="0.3" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {[0, 0.5, 1].map((t) => {
        const y = pad.top + innerH * (1 - t);
        return (
          <g key={t}>
            <line x1={pad.left} y1={y} x2={pad.left + innerW} y2={y}
              stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
            <text x={pad.left - 6} y={y + 4} textAnchor="end"
              fontSize="9" fill="rgba(255,255,255,0.25)">
              {t === 0 ? 0 : formatCompact(max * t)}
            </text>
          </g>
        );
      })}

      {/* Bars */}
      {data.map((d, i) => {
        const x = pad.left + (i / data.length) * innerW + 1;
        const barH = (d.value / max) * innerH;
        const y = pad.top + innerH - barH;
        return (
          <rect key={i} x={x} y={y} width={barW} height={barH}
            fill={`url(#${chartId})`} rx="2" />
        );
      })}

      {/* X-axis labels */}
      {data.map((d, i) => {
        if (i % labelStep !== 0 && i !== data.length - 1) return null;
        const x = pad.left + (i / data.length) * innerW + barW / 2 + 1;
        return (
          <text key={i} x={x} y={pad.top + innerH + 16}
            textAnchor="middle" fontSize="9" fill="rgba(255,255,255,0.3)">
            {d.date.slice(5)}
          </text>
        );
      })}
    </svg>
  );
}

function DonutChart({
  data,
  size = 140,
}: {
  data: { label: string; value: number; color: string }[];
  size?: number;
}) {
  const cx = size / 2;
  const cy = size / 2;
  const R = size / 2 - 10;
  const r = R * 0.58;

  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  let angle = -Math.PI / 2;

  const slices = data.map((d) => {
    const sweep = (d.value / total) * 2 * Math.PI;
    const x1 = cx + R * Math.cos(angle);
    const y1 = cy + R * Math.sin(angle);
    angle += sweep;
    const x2 = cx + R * Math.cos(angle);
    const y2 = cy + R * Math.sin(angle);
    const largeArc = sweep > Math.PI ? 1 : 0;

    const path = [
      `M ${cx} ${cy}`,
      `L ${x1} ${y1}`,
      `A ${R} ${R} 0 ${largeArc} 1 ${x2} ${y2}`,
      "Z",
    ].join(" ");

    // Inner cutout path
    const ix1 = cx + r * Math.cos(angle - sweep);
    const iy1 = cy + r * Math.sin(angle - sweep);
    const ix2 = cx + r * Math.cos(angle);
    const iy2 = cy + r * Math.sin(angle);
    const donut = [
      `M ${x1} ${y1}`,
      `A ${R} ${R} 0 ${largeArc} 1 ${x2} ${y2}`,
      `L ${ix2} ${iy2}`,
      `A ${r} ${r} 0 ${largeArc} 0 ${ix1} ${iy1}`,
      "Z",
    ].join(" ");

    return { ...d, donut };
  });

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size}>
      {slices.map((s, i) => (
        <path key={i} d={s.donut} fill={s.color} opacity={0.85} />
      ))}
      {/* Centre hole background */}
      <circle cx={cx} cy={cy} r={r - 1} fill="rgba(13,13,16,0.95)" />
      <text x={cx} y={cy - 4} textAnchor="middle" fontSize="14"
        fontWeight="700" fill="#f1f1f3">
        {data.length}
      </text>
      <text x={cx} y={cy + 11} textAnchor="middle" fontSize="8"
        fill="rgba(255,255,255,0.4)">
        models
      </text>
    </svg>
  );
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatCompact(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}m`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n % 1 === 0 ? String(Math.round(n)) : n.toFixed(2);
}

function formatCost(n: number) {
  if (n === 0) return "$0.00";
  if (n < 0.001) return `$${n.toFixed(5)}`;
  if (n < 0.01) return `$${n.toFixed(4)}`;
  if (n < 1) return `$${n.toFixed(3)}`;
  return `$${n.toFixed(2)}`;
}

function formatLatency(ms: number) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

function formatDuration(ms: number) {
  if (ms >= 60000) return `${(ms / 60000).toFixed(1)}m`;
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${ms.toFixed(0)}ms`;
}

const MODEL_COLORS = [
  "#818cf8", "#34d399", "#38bdf8", "#fbbf24",
  "#f472b6", "#a78bfa", "#fb923c", "#4ade80",
];

// ─── Main Component ───────────────────────────────────────────────────────────

export function Analytics({ projectId }: AnalyticsProps) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeChart, setActiveChart] = useState<"sessions" | "cost" | "tokens" | "errors" | "error_rate">("sessions");
  const [period, setPeriod] = useState<number>(30);
  const [modelMetric, setModelMetric] = useState<"calls" | "cost">("calls");

  const fetch = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      setData(await api.getAnalyticsWithPeriod(projectId, period));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetch(); }, [projectId, period]);

  if (!projectId) {
    return (
      <div style={styles.emptyProject}>
        <Activity size={32} style={{ color: "var(--text-muted)", marginBottom: 12 }} />
        <p style={{ fontSize: 15, color: "var(--text-muted)" }}>
          Select a project to view analytics.
        </p>
      </div>
    );
  }

  // ── Summary stat cards config ──────────────────────────────────────────
  const statCards = data
    ? [
        {
          icon: <BarChart2 size={18} />,
          iconColor: "#818cf8",
          iconBg: "rgba(99,102,241,0.12)",
          label: "Total Sessions",
          value: formatCompact(data.total_sessions),
          sub: `last ${data.period_days} days`,
          subColor: "var(--text-muted)",
        },
        {
          icon: <DollarSign size={18} />,
          iconColor: "#34d399",
          iconBg: "rgba(16,185,129,0.12)",
          label: "Total Cost",
          value: formatCost(data.total_cost_usd),
          sub: `${formatCompact(data.total_tokens)} tokens`,
          subColor: "var(--text-muted)",
        },
        {
          icon: <Clock size={18} />,
          iconColor: "#fbbf24",
          iconBg: "rgba(245,158,11,0.12)",
          label: "Avg Latency",
          value: formatLatency(data.avg_latency_ms),
          sub: `${formatCompact(data.total_events)} total events`,
          subColor: "var(--text-muted)",
        },
        {
          icon: <Clock size={18} />,
          iconColor: "#a78bfa",
          iconBg: "rgba(167,139,250,0.12)",
          label: "Avg Duration",
          value: data.avg_session_duration_ms ? formatDuration(data.avg_session_duration_ms) : "—",
          sub: "per agent session",
          subColor: "var(--text-muted)",
        },
        {
          icon: <AlertCircle size={18} />,
          iconColor: data.error_sessions > 0 ? "#f43f5e" : "#10b981",
          iconBg: data.error_sessions > 0 ? "rgba(244,63,94,0.12)" : "rgba(16,185,129,0.12)",
          label: "Error Sessions",
          value: String(data.error_sessions),
          sub: data.loop_sessions > 0 ? `${data.loop_sessions} loop issue${data.loop_sessions !== 1 ? "s" : ""}` : "No loops detected",
          subColor: data.loop_sessions > 0 ? "var(--color-warning)" : "var(--color-success)",
        },
      ]
    : [];

  const chartTabs: { key: typeof activeChart; label: string; color: string }[] = [
    { key: "sessions", label: "Sessions", color: "#818cf8" },
    { key: "cost",     label: "Cost",     color: "#34d399" },
    { key: "tokens",   label: "Tokens",   color: "#38bdf8" },
    { key: "errors",   label: "Errors",   color: "#f43f5e" },
    { key: "error_rate", label: "Error Rate", color: "#fb7185" },
  ];

  const activeTab = chartTabs.find(t => t.key === activeChart)!;

  const getChartData = () => {
    if (!data) return [];
    if (activeChart === "error_rate") {
      return (data.error_rate_daily ?? []).map((d) => ({
        date: d.date,
        value: d.error_rate * 100,
      }));
    }
    const key = activeChart === "cost" ? "cost_usd" : activeChart;
    return data.daily.map((d) => ({
      date: d.date,
      value: Number(d[key as keyof DailyMetric] || 0),
    }));
  };

  const sortedModels = [...(data?.top_models ?? [])].sort((a, b) => {
    return modelMetric === "calls" ? b.calls - a.calls : b.cost_usd - a.cost_usd;
  });

  const maxModelVal = sortedModels.length > 0
    ? (modelMetric === "calls" ? Math.max(...sortedModels.map(m => m.calls)) : Math.max(...sortedModels.map(m => m.cost_usd)))
    : 1;

  const donutData = sortedModels.map((m, i) => ({
    label: m.model,
    value: modelMetric === "calls" ? m.calls : m.cost_usd,
    color: MODEL_COLORS[i % MODEL_COLORS.length],
  }));

  return (
    <div style={styles.container} className="animated-fade-in">

      {/* ── Page header ── */}
      <div style={styles.pageHeader}>
        <div>
          <h1 style={styles.pageTitle}>Analytics</h1>
          <p style={styles.pageSub}>
            {period}-day performance metrics, cost trends, and model usage breakdown.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {/* Period Selector */}
          <div style={styles.periodGroup}>
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                style={{
                  ...styles.periodBtn,
                  background: period === d ? "var(--color-primary-glow)" : "transparent",
                  color: period === d ? "var(--color-primary-light)" : "var(--text-secondary)",
                  borderColor: period === d ? "rgba(99, 102, 241, 0.4)" : "var(--border-color)",
                }}
                onClick={() => setPeriod(d)}
                disabled={loading}
              >
                {d}d
              </button>
            ))}
          </div>

          <button
            className="btn btn-secondary"
            onClick={fetch}
            disabled={loading}
            style={{ gap: 8, padding: "9px 16px", fontSize: 13 }}
          >
            <RefreshCw size={14} className={loading ? "spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Stat cards ── */}
      {loading ? (
        <div style={styles.metricsGrid}>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="card skeleton" style={{ height: 100 }} />
          ))}
        </div>
      ) : data ? (
        <div style={styles.metricsGrid}>
          {statCards.map((m, i) => (
            <div key={i} className="card" style={{ ...styles.metricCard, animationDelay: `${i * 60}ms` }}>
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
      ) : null}

      {/* ── Trend chart card ── */}
      <div className="card" style={styles.chartCard}>
        <div style={styles.chartHeader}>
          <div>
            <h2 style={styles.chartTitle}>Daily Trends</h2>
            <p style={styles.chartSub}>Last 30 days</p>
          </div>
          {/* Chart tab switcher */}
          <div style={styles.chartTabs}>
            {chartTabs.map((tab) => (
              <button
                key={tab.key}
                style={{
                  ...styles.chartTab,
                  background: activeChart === tab.key ? "var(--color-primary-glow)" : "transparent",
                  color: activeChart === tab.key ? tab.color : "var(--text-secondary)",
                  borderColor: activeChart === tab.key ? `${tab.color}44` : "transparent",
                }}
                onClick={() => setActiveChart(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div style={styles.chartBody}>
          {loading ? (
            <div className="skeleton" style={{ height: 140, borderRadius: 8 }} />
          ) : data ? (
            activeChart === "cost" || activeChart === "error_rate" ? (
              <BarChartSVG data={getChartData()} color={activeTab.color} height={140} />
            ) : (
              <AreaChart data={getChartData()} color={activeTab.color} height={140} />
            )
          ) : null}
        </div>

        {/* Mini summary row below chart */}
        {data && (
          <div style={styles.chartFooter}>
            {[
              { label: "Peak day (sessions)", value: formatCompact(Math.max(...data.daily.map(d => d.sessions))) },
              { label: "Peak day (cost)", value: formatCost(Math.max(...data.daily.map(d => d.cost_usd))) },
              { label: "Peak day (tokens)", value: formatCompact(Math.max(...data.daily.map(d => d.tokens))) },
              { label: "Active days", value: String(data.daily.filter(d => d.sessions > 0).length) },
            ].map((s, i) => (
              <div key={i} style={styles.chartFooterItem}>
                <span style={styles.chartFooterLabel}>{s.label}</span>
                <span style={styles.chartFooterValue}>{s.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Bottom two-column: Models + Health ── */}
      <div style={styles.bottomGrid}>

        {/* Model breakdown */}
        <div className="card" style={styles.panelCard}>
          <div style={{ ...styles.panelHeader, justifyContent: "space-between", alignItems: "center", display: "flex", width: "100%" }}>
            <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
              <div style={{ ...styles.panelIcon, background: "rgba(99,102,241,0.12)" }}>
                <Cpu size={16} style={{ color: "var(--color-primary-light)" }} />
              </div>
              <div>
                <h2 style={styles.panelTitle}>Model Usage</h2>
                <p style={styles.panelSub}>
                  {modelMetric === "calls" ? "Top models by call volume" : "Top models by total cost"}
                </p>
              </div>
            </div>
            {/* Metric Switcher */}
            <div style={styles.miniTabs}>
              {(["calls", "cost"] as const).map((m) => (
                <button
                  key={m}
                  style={{
                    ...styles.miniTab,
                    background: modelMetric === m ? "var(--color-primary-glow)" : "transparent",
                    color: modelMetric === m ? "var(--color-primary-light)" : "var(--text-secondary)",
                    borderColor: modelMetric === m ? "rgba(99, 102, 241, 0.3)" : "transparent",
                  }}
                  onClick={() => setModelMetric(m)}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[...Array(3)].map((_, i) => <div key={i} className="skeleton" style={{ height: 44, borderRadius: 8 }} />)}
            </div>
          ) : sortedModels.length ? (
            <div style={styles.modelLayout}>
              {/* Donut chart */}
              <div style={{ flexShrink: 0 }}>
                <DonutChart data={donutData} size={130} />
              </div>

              {/* Legend + rows */}
              <div style={styles.modelList}>
                {sortedModels.map((m, i) => {
                  const color = MODEL_COLORS[i % MODEL_COLORS.length];
                  const barVal = modelMetric === "calls" ? m.calls : m.cost_usd;
                  const barPercent = (barVal / maxModelVal) * 100;
                  return (
                    <div key={m.model} style={styles.modelRow}>
                      <div style={styles.modelRowTop}>
                        <div style={styles.modelRowLeft}>
                          <div style={{ ...styles.modelDot, background: color }} />
                          <span style={styles.modelName}>{m.model}</span>
                        </div>
                        <div style={styles.modelRowRight}>
                          <span style={styles.modelCallCount}>{formatCompact(m.calls)} calls</span>
                          <span style={{ ...styles.modelCost, color }}>{formatCost(m.cost_usd)}</span>
                        </div>
                      </div>
                      {/* Progress bar */}
                      <div style={styles.modelBar}>
                        <div style={{
                          ...styles.modelBarFill,
                          width: `${barPercent}%`,
                          background: color,
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div style={styles.emptyPanel}>
              <Zap size={22} style={{ color: "var(--text-muted)", marginBottom: 8 }} />
              <p>No model usage data yet.</p>
            </div>
          )}
        </div>

        {/* Health & loop summary */}
        <div className="card" style={styles.panelCard}>
          <div style={styles.panelHeader}>
            <div style={{ ...styles.panelIcon, background: "rgba(244,63,94,0.1)" }}>
              <ShieldAlert size={16} style={{ color: "var(--color-error)" }} />
            </div>
            <div>
              <h2 style={styles.panelTitle}>Agent Health</h2>
              <p style={styles.panelSub}>Errors, loops, and reliability</p>
            </div>
          </div>

          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 52, borderRadius: 8 }} />)}
            </div>
          ) : data ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                {
                  icon: <BarChart2 size={16} />,
                  iconBg: "rgba(99,102,241,0.12)", iconColor: "#818cf8",
                  label: "Total Sessions",
                  value: formatCompact(data.total_sessions),
                  sub: "in last 30 days",
                },
                {
                  icon: <AlertCircle size={16} />,
                  iconBg: data.error_sessions > 0 ? "rgba(244,63,94,0.12)" : "rgba(16,185,129,0.12)",
                  iconColor: data.error_sessions > 0 ? "#f43f5e" : "#10b981",
                  label: "Error Sessions",
                  value: `${data.error_sessions}`,
                  sub: data.total_sessions > 0
                    ? `${((data.error_sessions / data.total_sessions) * 100).toFixed(1)}% error rate`
                    : "—",
                },
                {
                  icon: <RotateCcw size={16} />,
                  iconBg: data.loop_sessions > 0 ? "rgba(245,158,11,0.12)" : "rgba(16,185,129,0.12)",
                  iconColor: data.loop_sessions > 0 ? "#fbbf24" : "#10b981",
                  label: "Loop Issues",
                  value: `${data.loop_sessions}`,
                  sub: data.loop_sessions > 0 ? "sessions with repetitive patterns" : "No loops detected",
                },
                {
                  icon: <TrendingUp size={16} />,
                  iconBg: "rgba(56,189,248,0.12)", iconColor: "#38bdf8",
                  label: "Avg Latency",
                  value: formatLatency(data.avg_latency_ms),
                  sub: "per LLM/tool call",
                },
              ].map((row, i) => (
                <div key={i} style={styles.healthRow}>
                  <div style={{ ...styles.healthIcon, background: row.iconBg, color: row.iconColor }}>
                    {row.icon}
                  </div>
                  <div style={styles.healthInfo}>
                    <span style={styles.healthLabel}>{row.label}</span>
                    <span style={styles.healthSub}>{row.sub}</span>
                  </div>
                  <span style={{ ...styles.healthValue, color: row.iconColor }}>
                    {row.value}
                  </span>
                </div>
              ))}

              {/* Error sparkline */}
              {data.total_sessions > 0 && (
                <div style={styles.errorSparkWrap}>
                  <span style={styles.sparkLabel}>Error sessions over time</span>
                  <BarChartSVG
                    data={data.daily}
                    valueKey="errors"
                    color="#f43f5e"
                    height={60}
                  />
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────
const styles: Record<string, React.CSSProperties> = {
  container: { padding: "36px 40px", display: "flex", flexDirection: "column", flex: 1, gap: 28 },

  emptyProject: {
    display: "flex", flexDirection: "column", alignItems: "center",
    justifyContent: "center", flex: 1, padding: 60,
  },

  pageHeader: { display: "flex", alignItems: "flex-start", justifyContent: "space-between" },
  periodGroup: {
    display: "flex",
    background: "var(--bg-glass)",
    border: "1px solid var(--border-color)",
    borderRadius: 10,
    padding: 3,
    gap: 2,
  },
  periodBtn: {
    padding: "6px 12px",
    fontSize: 12,
    fontWeight: 600,
    border: "1px solid transparent",
    borderRadius: 8,
    cursor: "pointer",
    transition: "all 0.15s",
    outline: "none",
    fontFamily: "var(--font-sans)",
  },
  pageTitle: {
    fontFamily: "var(--font-heading)", fontSize: 30, fontWeight: 700, letterSpacing: "-0.5px",
    background: "linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%)",
    WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
    marginBottom: 6,
  },
  pageSub: { fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.5 },

  metricsGrid: { display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 18 },
  metricCard: { padding: 0, overflow: "hidden", cursor: "default", position: "relative" },
  metricAccent: { position: "absolute", top: 0, left: 0, right: 0, height: 2, borderRadius: "14px 14px 0 0" },
  metricBody: { display: "flex", gap: 16, alignItems: "center", padding: "20px 22px" },
  metricIconWrap: { width: 44, height: 44, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 },
  metricInfo: { display: "flex", flexDirection: "column", gap: 3 },
  metricLabel: { fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.6px" },
  metricValue: { fontFamily: "var(--font-heading)", fontSize: 26, fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.15 },
  metricSub: { fontSize: 11, fontWeight: 500 },

  chartCard: { padding: 0, overflow: "hidden" },
  chartHeader: { display: "flex", alignItems: "flex-start", justifyContent: "space-between", padding: "20px 24px 16px" },
  chartTitle: { fontFamily: "var(--font-heading)", fontSize: 16, fontWeight: 700, color: "var(--text-primary)", marginBottom: 3 },
  chartSub: { fontSize: 12, color: "var(--text-secondary)" },
  chartTabs: { display: "flex", background: "var(--bg-glass)", border: "1px solid var(--border-color)", borderRadius: 10, padding: 4, gap: 2 },
  chartTab: {
    padding: "5px 14px", fontSize: 12, fontWeight: 600,
    border: "1px solid transparent", borderRadius: 8,
    cursor: "pointer", transition: "all 0.15s",
    outline: "none", fontFamily: "var(--font-sans)",
  },
  chartBody: { padding: "0 24px 4px" },
  chartFooter: {
    display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
    borderTop: "1px solid var(--border-color)",
    background: "rgba(0,0,0,0.15)",
  },
  chartFooterItem: {
    display: "flex", flexDirection: "column", gap: 3,
    padding: "14px 20px",
    borderRight: "1px solid var(--border-color)",
  },
  chartFooterLabel: { fontSize: 10, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" },
  chartFooterValue: { fontSize: 15, fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-mono)" },

  bottomGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, alignItems: "start" },
  panelCard: { padding: 24, display: "flex", flexDirection: "column", gap: 20 },
  panelHeader: { display: "flex", alignItems: "flex-start", gap: 14 },
  panelIcon: { width: 36, height: 36, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 },
  panelTitle: { fontFamily: "var(--font-heading)", fontSize: 16, fontWeight: 700, color: "var(--text-primary)", marginBottom: 3 },
  panelSub: { fontSize: 12, color: "var(--text-secondary)" },

  modelLayout: { display: "flex", gap: 20, alignItems: "flex-start" },
  modelList: { display: "flex", flexDirection: "column", gap: 10, flex: 1, minWidth: 0 },
  modelRow: { display: "flex", flexDirection: "column", gap: 5 },
  modelRowTop: { display: "flex", alignItems: "center", justifyContent: "space-between" },
  modelRowLeft: { display: "flex", alignItems: "center", gap: 8 },
  modelDot: { width: 8, height: 8, borderRadius: "50%", flexShrink: 0 },
  modelName: { fontSize: 12, fontWeight: 600, color: "var(--text-primary)", fontFamily: "var(--font-mono)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 120 },
  modelRowRight: { display: "flex", alignItems: "center", gap: 10, flexShrink: 0 },
  modelCallCount: { fontSize: 11, color: "var(--text-secondary)", fontWeight: 500 },
  modelCost: { fontSize: 11, fontWeight: 700, fontFamily: "var(--font-mono)" },
  modelBar: { height: 3, background: "rgba(255,255,255,0.06)", borderRadius: 99, overflow: "hidden" },
  modelBarFill: { height: "100%", borderRadius: 99, transition: "width 0.4s ease" },

  emptyPanel: { display: "flex", flexDirection: "column", alignItems: "center", padding: "32px 0", color: "var(--text-muted)", fontSize: 13 },

  healthRow: { display: "flex", alignItems: "center", gap: 12, padding: "10px 14px", background: "var(--bg-glass)", border: "1px solid var(--border-color)", borderRadius: 10 },
  healthIcon: { width: 32, height: 32, borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 },
  healthInfo: { display: "flex", flexDirection: "column", gap: 2, flex: 1 },
  healthLabel: { fontSize: 13, fontWeight: 600, color: "var(--text-primary)" },
  healthSub: { fontSize: 11, color: "var(--text-muted)" },
  healthValue: { fontSize: 18, fontWeight: 800, fontFamily: "var(--font-mono)", flexShrink: 0 },

  errorSparkWrap: { display: "flex", flexDirection: "column", gap: 6, padding: "12px 14px", background: "rgba(244,63,94,0.04)", border: "1px solid rgba(244,63,94,0.12)", borderRadius: 10 },
  sparkLabel: { fontSize: 10, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" },
};
