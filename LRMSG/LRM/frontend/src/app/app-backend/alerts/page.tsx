"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Alert } from "@/types/alerts";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";
import {
  Bell,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
  ArrowRight,
  ServerCrash,
  Search,
  Shield,
  MapPin,
} from "lucide-react";

const SEVERITY_OPTIONS = [
  { value: "all", label: "All" },
  { value: "CRITICAL", label: "Critical" },
  { value: "HIGH", label: "High" },
  { value: "MODERATE", label: "Moderate" },
  { value: "LOW", label: "Low" },
];

const STATUS_OPTIONS = [
  { value: "all", label: "All" },
  { value: "ACTIVE", label: "Active" },
  { value: "ACKNOWLEDGED", label: "Acknowledged" },
  { value: "UNDER_RESPONSE", label: "Under Response" },
  { value: "RESOLVED", label: "Resolved" },
];

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "var(--red)",
  HIGH: "#f97316",
  MODERATE: "var(--amber)",
  LOW: "var(--green)",
};

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: "var(--red)",
  ACKNOWLEDGED: "var(--amber)",
  UNDER_RESPONSE: "#3b82f6",
  RESOLVED: "var(--green)",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  ACTIVE: <AlertTriangle size={12} />,
  ACKNOWLEDGED: <Clock size={12} />,
  UNDER_RESPONSE: <Shield size={12} />,
  RESOLVED: <CheckCircle size={12} />,
};

function SeverityBadge({ severity }: { severity: string }) {
  const color = SEVERITY_COLORS[severity] || "var(--text-secondary)";
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "3px 10px",
        borderRadius: "12px",
        fontFamily: "'DM Mono', monospace",
        fontSize: "10px",
        fontWeight: 600,
        letterSpacing: "0.5px",
        color,
        background: `${color}15`,
        border: `1px solid ${color}30`,
        textTransform: "uppercase",
      }}
    >
      {severity}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "var(--text-secondary)";
  const icon = STATUS_ICONS[status] || null;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "3px 10px",
        borderRadius: "12px",
        fontFamily: "'DM Mono', monospace",
        fontSize: "10px",
        fontWeight: 600,
        letterSpacing: "0.5px",
        color,
        background: `${color}15`,
        border: `1px solid ${color}30`,
        textTransform: "uppercase",
      }}
    >
      {icon}
      {status}
    </span>
  );
}

function ProbabilityBar({ probability }: { probability: number | null }) {
  if (probability === null || probability === undefined) return null;
  const pct = Math.min(Math.max(probability, 0), 100);
  const color =
    pct >= 95
      ? "var(--red)"
      : pct >= 60
        ? "#f97316"
        : pct >= 30
          ? "var(--amber)"
          : "var(--green)";
  return (
    <div
      style={{
        width: "100%",
        height: "6px",
        background: "var(--line)",
        borderRadius: "3px",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${pct}%`,
          height: "100%",
          background: color,
          borderRadius: "3px",
          transition: "width 0.3s",
        }}
      />
    </div>
  );
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  async function loadAlerts() {
    try {
      const data = await apiFetch<Alert[]>("/api/alerts/list?limit=500");
      setAlerts(data);
      setError(null);
    } catch {
      setError("Failed to load alerts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAlerts();
  }, []);

  const filtered = useMemo(() => {
    let result = alerts;
    if (severityFilter !== "all") {
      result = result.filter((a) => a.severity === severityFilter);
    }
    if (statusFilter !== "all") {
      result = result.filter((a) => a.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          (a.location_name && a.location_name.toLowerCase().includes(q)) ||
          (a.district && a.district.toLowerCase().includes(q)) ||
          (a.state && a.state.toLowerCase().includes(q)) ||
          (a.location_id && a.location_id.toLowerCase().includes(q))
      );
    }
    return result;
  }, [alerts, severityFilter, statusFilter, searchQuery]);

  const severityCounts = useMemo(() => {
    const counts: Record<string, number> = { all: alerts.length };
    for (const opt of SEVERITY_OPTIONS) {
      if (opt.value !== "all") counts[opt.value] = 0;
    }
    for (const a of alerts) {
      if (counts[a.severity] !== undefined) counts[a.severity]++;
    }
    return counts;
  }, [alerts]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { all: alerts.length };
    for (const opt of STATUS_OPTIONS) {
      if (opt.value !== "all") counts[opt.value] = 0;
    }
    for (const a of alerts) {
      if (counts[a.status] !== undefined) counts[a.status]++;
    }
    return counts;
  }, [alerts]);

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Alerts</h1>
          <p>Loading alert data...</p>
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: "16px",
          }}
        >
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="card"
              style={{ borderTop: "3px solid var(--line)" }}
            >
              <div
                className="skeleton"
                style={{ width: "60%", height: 12, marginBottom: 12 }}
              />
              <div
                className="skeleton"
                style={{ width: "80%", height: 16, marginBottom: 10 }}
              />
              <div
                className="skeleton"
                style={{ width: "100%", height: 10, marginBottom: 6 }}
              />
              <div
                className="skeleton"
                style={{ width: "40%", height: 10, marginTop: 12 }}
              />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Alerts</h1>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "24px",
            background: "#fee2e2",
            borderRadius: "8px",
            border: "1px solid #fca5a5",
            fontFamily: "'DM Mono', monospace",
            fontSize: "13px",
            color: "#991b1b",
          }}
        >
          <ServerCrash size={20} />
          {error}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="analytics-header">
        <h1>Alerts</h1>
        <p>
          {alerts.length} total alerts &middot; Monitor and respond to
          landslide risk alerts
        </p>
      </div>

      {/* Summary counts */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
          gap: "12px",
          marginBottom: "24px",
        }}
      >
        {SEVERITY_OPTIONS.filter((o) => o.value !== "all").map((opt) => (
          <div
            key={opt.value}
            className="card"
            style={{
              borderTop: `3px solid ${SEVERITY_COLORS[opt.value]}`,
              padding: "16px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: "10px",
                fontWeight: 600,
                color: "var(--text-secondary)",
                letterSpacing: "1px",
                textTransform: "uppercase",
                marginBottom: "4px",
              }}
            >
              {opt.label}
            </div>
            <div
              style={{
                fontFamily: "'Space Grotesk', sans-serif",
                fontSize: "24px",
                fontWeight: 700,
                color: SEVERITY_COLORS[opt.value],
              }}
            >
              {severityCounts[opt.value] ?? 0}
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          marginBottom: "24px",
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "8px 12px",
            background: "var(--surface)",
            border: "1px solid var(--line)",
            borderRadius: "4px",
            flex: "1 1 200px",
            maxWidth: "300px",
          }}
        >
          <Search
            size={14}
            style={{ color: "var(--text-secondary)", flexShrink: 0 }}
          />
          <input
            type="text"
            placeholder="Search location, district, state..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              border: "none",
              background: "transparent",
              outline: "none",
              fontFamily: "'DM Mono', monospace",
              fontSize: "12px",
              color: "var(--text-primary)",
              width: "100%",
            }}
          />
        </div>

        <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
          {SEVERITY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSeverityFilter(opt.value)}
              style={{
                padding: "6px 12px",
                borderRadius: "4px",
                border:
                  severityFilter === opt.value
                    ? `1px solid ${opt.value === "all" ? "var(--accent)" : SEVERITY_COLORS[opt.value]}`
                    : "1px solid var(--line)",
                background:
                  severityFilter === opt.value
                    ? opt.value === "all"
                      ? "var(--accent)"
                      : SEVERITY_COLORS[opt.value]
                    : "transparent",
                color:
                  severityFilter === opt.value
                    ? "#fff"
                    : "var(--text-secondary)",
                fontFamily: "'DM Mono', monospace",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {opt.label} ({severityCounts[opt.value] ?? 0})
            </button>
          ))}
        </div>

        <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              style={{
                padding: "6px 12px",
                borderRadius: "4px",
                border:
                  statusFilter === opt.value
                    ? `1px solid ${opt.value === "all" ? "var(--accent)" : STATUS_COLORS[opt.value]}`
                    : "1px solid var(--line)",
                background:
                  statusFilter === opt.value
                    ? opt.value === "all"
                      ? "var(--accent)"
                      : STATUS_COLORS[opt.value]
                    : "transparent",
                color:
                  statusFilter === opt.value
                    ? "#fff"
                    : "var(--text-secondary)",
                fontFamily: "'DM Mono', monospace",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {opt.label} ({statusCounts[opt.value] ?? 0})
            </button>
          ))}
        </div>
      </div>

      {/* Alert cards */}
      {filtered.length === 0 ? (
        <div
          style={{
            padding: "48px 24px",
            textAlign: "center",
            background: "var(--surface)",
            borderRadius: "8px",
            border: "1px solid var(--line)",
          }}
        >
          <Bell
            size={32}
            style={{ color: "var(--text-secondary)", marginBottom: "12px" }}
          />
          <div
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "16px",
              fontWeight: 600,
              color: "var(--text-primary)",
              marginBottom: "8px",
            }}
          >
            No alerts found
          </div>
          <div
            style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: "12px",
              color: "var(--text-secondary)",
            }}
          >
            {searchQuery
              ? "Try adjusting your search or filter criteria"
              : severityFilter !== "all" || statusFilter !== "all"
                ? "No alerts match the current filters"
                : "No alerts have been generated yet"}
          </div>
        </div>
      ) : (
        <Motion initial="hidden" animate="visible" variants={staggerContainer}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
              gap: "16px",
            }}
          >
            {filtered.map((alert) => (
              <Motion key={alert.id} variants={cardReveal}>
                <div
                  className="card"
                  style={{
                    borderTop: `3px solid ${SEVERITY_COLORS[alert.severity] || "var(--line)"}`,
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "12px",
                    }}
                  >
                    <div style={{ display: "flex", gap: "6px" }}>
                      <SeverityBadge severity={alert.severity} />
                      <StatusBadge status={alert.status} />
                    </div>
                    <Link
                      href={`/app-backend/alerts/${alert.id}`}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                        fontFamily: "'DM Mono', monospace",
                        fontSize: "11px",
                        color: "var(--accent)",
                        textDecoration: "none",
                      }}
                    >
                      Details <ArrowRight size={12} />
                    </Link>
                  </div>

                  <div style={{ marginBottom: "12px" }}>
                    <div
                      style={{
                        fontFamily: "'Space Grotesk', sans-serif",
                        fontSize: "15px",
                        fontWeight: 600,
                        color: "var(--text-primary)",
                        marginBottom: "2px",
                      }}
                    >
                      {alert.location_name || "Unknown Location"}
                    </div>
                    <div
                      style={{
                        fontFamily: "'DM Mono', monospace",
                        fontSize: "11px",
                        color: "var(--text-secondary)",
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                      }}
                    >
                      <MapPin size={11} />
                      {[
                        alert.district,
                        alert.state,
                      ]
                        .filter(Boolean)
                        .join(", ") || "No location details"}
                    </div>
                  </div>

                  {alert.risk_probability !== null &&
                    alert.risk_probability !== undefined && (
                      <div style={{ marginBottom: "12px" }}>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            fontFamily: "'DM Mono', monospace",
                            fontSize: "10px",
                            color: "var(--text-secondary)",
                            marginBottom: "4px",
                          }}
                        >
                          <span>Risk Probability</span>
                          <span>{alert.risk_probability}%</span>
                        </div>
                        <ProbabilityBar probability={alert.risk_probability} />
                      </div>
                    )}

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "8px",
                      marginBottom: "12px",
                    }}
                  >
                    <div
                      style={{
                        textAlign: "center",
                        padding: "8px",
                        background: "var(--surface)",
                        borderRadius: "4px",
                      }}
                    >
                      <div
                        style={{
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "10px",
                          color: "var(--text-secondary)",
                        }}
                      >
                        PRIORITY
                      </div>
                      <div
                        style={{
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "11px",
                          fontWeight: 600,
                          color: "var(--text-primary)",
                          marginTop: "2px",
                          textTransform: "uppercase",
                        }}
                      >
                        {alert.response_priority || "—"}
                      </div>
                    </div>
                    <div
                      style={{
                        textAlign: "center",
                        padding: "8px",
                        background: "var(--surface)",
                        borderRadius: "4px",
                      }}
                    >
                      <div
                        style={{
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "10px",
                          color: "var(--text-secondary)",
                        }}
                      >
                        TRIGGER
                      </div>
                      <div
                        style={{
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "11px",
                          fontWeight: 600,
                          color: "var(--text-primary)",
                          marginTop: "2px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {alert.trigger || "—"}
                      </div>
                    </div>
                  </div>

                  <div
                    style={{
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "10px",
                      color: "var(--text-secondary)",
                      display: "flex",
                      justifyContent: "space-between",
                    }}
                  >
                    <span>
                      {alert.created_at
                        ? new Date(alert.created_at).toLocaleDateString()
                        : "—"}
                    </span>
                    <span>{alert.id.slice(0, 8)}...</span>
                  </div>
                </div>
              </Motion>
            ))}
          </div>
        </Motion>
      )}

      <div
        style={{
          marginTop: "24px",
          padding: "16px",
          background: "var(--surface)",
          border: "1px solid var(--line)",
          borderRadius: "4px",
          fontFamily: "'DM Mono', monospace",
          fontSize: "10px",
          letterSpacing: "1px",
          color: "var(--text-secondary)",
        }}
      >
        NOTE: Authentication/RBAC is not yet implemented. Alert actions are not
        secured.
      </div>
    </div>
  );
}

