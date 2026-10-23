"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Alert } from "@/types/alerts";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";

interface DbAlert extends Alert {
  incident_id?: string | null;
  triggered_at?: string | null;
}
import {
  ArrowLeft,
  CheckCircle,
  Clock,
  XCircle,
  Shield,
  AlertTriangle,
  ServerCrash,
  MapPin,
  CloudRain,
  Mountain,
  Layers,
  Route,
  Bell,
  Activity,
  Zap,
} from "lucide-react";

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
  ACTIVE: <AlertTriangle size={14} />,
  ACKNOWLEDGED: <Clock size={14} />,
  UNDER_RESPONSE: <Shield size={14} />,
  RESOLVED: <CheckCircle size={14} />,
};

function DetailRow({
  label,
  value,
  icon,
}: {
  label: string;
  value: React.ReactNode;
  icon?: React.ReactNode;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "10px 14px",
        background: "var(--surface)",
        borderRadius: "4px",
        border: "1px solid var(--line)",
      }}
    >
      <span
        style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: "11px",
          fontWeight: 600,
          color: "var(--text-primary)",
          display: "flex",
          alignItems: "center",
          gap: "6px",
        }}
      >
        {icon}
        {label}
      </span>
      <span
        style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: "11px",
          color: "var(--text-secondary)",
          textAlign: "right",
          wordBreak: "break-all",
          maxWidth: "60%",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function TimelineEntry({
  label,
  timestamp,
  color,
}: {
  label: string;
  timestamp: string | null | undefined;
  color: string;
}) {
  if (!timestamp) return null;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "8px 0",
      }}
    >
      <div
        style={{
          width: "10px",
          height: "10px",
          borderRadius: "50%",
          background: color,
          flexShrink: 0,
        }}
      />
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: "11px",
            fontWeight: 600,
            color: "var(--text-primary)",
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontFamily: "'DM Mono', monospace",
            fontSize: "10px",
            color: "var(--text-secondary)",
          }}
        >
          {new Date(timestamp).toLocaleString()}
        </div>
      </div>
    </div>
  );
}

export default function AlertDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [alert, setAlert] = useState<DbAlert | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transitioning, setTransitioning] = useState(false);

  async function loadAlert() {
    try {
      const data = await apiFetch<DbAlert>(`/api/alerts/list/${id}`);
      setAlert(data);
      setError(null);
    } catch {
      setError("Failed to load alert");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (id) loadAlert();
  }, [id]);

  async function transitionStatus(action: "acknowledge" | "responding" | "resolve") {
    if (!alert) return;
    setTransitioning(true);
    try {
      await apiFetch(`/api/alerts/${alert.id}/${action}`, {
        method: "POST",
      });
      await loadAlert();
    } catch {
      // Status transition failed — keep current state
    } finally {
      setTransitioning(false);
    }
  }

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Alert Detail</h1>
          <p>Loading alert data...</p>
        </div>
        <div style={{ display: "grid", gap: "16px" }}>
          {[1, 2, 3].map((i) => (
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
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !alert) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Alert Detail</h1>
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
          {error || "Alert not found"}
        </div>
        <Link
          href="/app-backend/alerts"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            marginTop: "16px",
            fontFamily: "'DM Mono', monospace",
            fontSize: "12px",
            color: "var(--accent)",
            textDecoration: "none",
          }}
        >
          <ArrowLeft size={14} /> Back to Alerts
        </Link>
      </div>
    );
  }

  const severityColor = SEVERITY_COLORS[alert.severity] || "var(--text-secondary)";
  const statusColor = STATUS_COLORS[alert.status] || "var(--text-secondary)";

  return (
    <div>
      <Link
        href="/app-backend/alerts"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "6px",
          marginBottom: "16px",
          fontFamily: "'DM Mono', monospace",
          fontSize: "12px",
          color: "var(--accent)",
          textDecoration: "none",
        }}
      >
        <ArrowLeft size={14} /> Back to Alerts
      </Link>

      <Motion initial="hidden" animate="visible" variants={staggerContainer}>
        {/* Header */}
        <Motion variants={cardReveal}>
          <div
            className="card"
            style={{ borderTop: `3px solid ${severityColor}`, marginBottom: "16px" }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                marginBottom: "12px",
              }}
            >
              <div style={{ display: "flex", gap: "8px" }}>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    padding: "4px 12px",
                    borderRadius: "12px",
                    fontFamily: "'DM Mono', monospace",
                    fontSize: "11px",
                    fontWeight: 600,
                    letterSpacing: "0.5px",
                    color: severityColor,
                    background: `${severityColor}15`,
                    border: `1px solid ${severityColor}30`,
                    textTransform: "uppercase",
                  }}
                >
                  {alert.severity}
                </span>
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    padding: "4px 12px",
                    borderRadius: "12px",
                    fontFamily: "'DM Mono', monospace",
                    fontSize: "11px",
                    fontWeight: 600,
                    letterSpacing: "0.5px",
                    color: statusColor,
                    background: `${statusColor}15`,
                    border: `1px solid ${statusColor}30`,
                    textTransform: "uppercase",
                  }}
                >
                  {STATUS_ICONS[alert.status]}
                  {alert.status}
                </span>
              </div>
            </div>

            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "20px", fontWeight: 700, color: "var(--text-primary)", marginBottom: "8px" }}>
              {alert.location_name || "Unknown Location"}
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-secondary)", marginBottom: "4px" }}>
              <MapPin size={14} />
              {alert.district && alert.state
                ? `${alert.district}, ${alert.state}`
                : alert.district || alert.state || "No location details"}
            </div>

            {alert.location_id && (
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)", opacity: 0.7 }}>
                ID: {alert.location_id}
              </div>
            )}

            {/* Status actions */}
            {alert.status !== "RESOLVED" && (
              <div style={{ display: "flex", gap: "8px", marginTop: "16px", flexWrap: "wrap" }}>
                {alert.status === "ACTIVE" && (
                  <button
                    onClick={() => transitionStatus("acknowledge")}
                    disabled={transitioning}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "4px",
                      border: "1px solid var(--amber)",
                      background: "var(--amber)",
                      color: "#fff",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "11px",
                      fontWeight: 600,
                      cursor: transitioning ? "not-allowed" : "pointer",
                      opacity: transitioning ? 0.6 : 1,
                    }}
                  >
                    Acknowledge
                  </button>
                )}
                {(alert.status === "ACTIVE" || alert.status === "ACKNOWLEDGED") && (
                  <button
                    onClick={() => transitionStatus("responding")}
                    disabled={transitioning}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "4px",
                      border: "1px solid #3b82f6",
                      background: "#3b82f6",
                      color: "#fff",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "11px",
                      fontWeight: 600,
                      cursor: transitioning ? "not-allowed" : "pointer",
                      opacity: transitioning ? 0.6 : 1,
                    }}
                  >
                    Mark Under Response
                  </button>
                )}
                <button
                  onClick={() => transitionStatus("resolve")}
                  disabled={transitioning}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "4px",
                    border: "1px solid var(--green)",
                    background: "var(--green)",
                    color: "#fff",
                    fontFamily: "'DM Mono', monospace",
                    fontSize: "11px",
                    fontWeight: 600,
                    cursor: transitioning ? "not-allowed" : "pointer",
                    opacity: transitioning ? 0.6 : 1,
                  }}
                >
                  Resolve Alert
                </button>
              </div>
            )}

            {alert.status === "RESOLVED" && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  marginTop: "16px",
                  padding: "8px 14px",
                  background: "#dcfce7",
                  borderRadius: "4px",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  fontWeight: 600,
                  color: "#166534",
                }}
              >
                <CheckCircle size={14} />
                ALERT RESOLVED
              </div>
            )}
          </div>
        </Motion>

        {/* Risk Information */}
        <Motion variants={cardReveal}>
          <div className="card" style={{ borderTop: `3px solid ${severityColor}`, marginBottom: "16px" }}>
            <p className="eyebrow" style={{ marginBottom: "12px" }}>RISK INFORMATION</p>
            <div style={{ display: "grid", gap: "8px" }}>
              <DetailRow
                label="Risk Probability"
                value={alert.risk_probability !== null ? `${alert.risk_probability}%` : "—"}
                icon={<Activity size={14} />}
              />
              <DetailRow
                label="Response Priority"
                value={alert.response_priority || "—"}
                icon={<Zap size={14} />}
              />
              <DetailRow
                label="Trigger"
                value={alert.trigger || "—"}
                icon={<AlertTriangle size={14} />}
              />
            </div>
          </div>
        </Motion>

        {/* Conditions */}
        <Motion variants={cardReveal}>
          <div className="card" style={{ borderTop: "3px solid #3b82f6", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ marginBottom: "12px" }}>CONDITIONS</p>
            <div style={{ display: "grid", gap: "8px" }}>
              <DetailRow
                label="Rainfall"
                value={alert.rainfall !== null ? `${alert.rainfall} mm` : "—"}
                icon={<CloudRain size={14} />}
              />
              <DetailRow
                label="Soil Condition"
                value={alert.soil_condition !== null ? alert.soil_condition.toFixed(2) : "—"}
                icon={<Layers size={14} />}
              />
              <DetailRow
                label="Slope Condition"
                value={alert.slope_condition !== null ? `${alert.slope_condition}°` : "—"}
                icon={<Mountain size={14} />}
              />
              <DetailRow
                label="Road Status"
                value={alert.road_status || "—"}
                icon={<Route size={14} />}
              />
            </div>
          </div>
        </Motion>

        {/* Contributing Factors */}
        {alert.contributing_factors && (
          <Motion variants={cardReveal}>
            <div className="card" style={{ borderTop: "3px solid var(--amber)", marginBottom: "16px" }}>
              <p className="eyebrow" style={{ marginBottom: "12px" }}>CONTRIBUTING FACTORS</p>
              <div
                style={{
                  padding: "12px 14px",
                  background: "var(--surface)",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "12px",
                  color: "var(--text-primary)",
                  lineHeight: 1.6,
                }}
              >
                {alert.contributing_factors}
              </div>
            </div>
          </Motion>
        )}

        {/* Incident & Notifications */}
        <Motion variants={cardReveal}>
          <div className="card" style={{ borderTop: "3px solid var(--text-secondary)", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ marginBottom: "12px" }}>INCIDENT & NOTIFICATIONS</p>
            <div style={{ display: "grid", gap: "8px" }}>
              <DetailRow
                label="Incident ID"
                value={alert.incident_id || "—"}
                icon={<Activity size={14} />}
              />
            </div>

            {alert.notifications && Object.keys(alert.notifications).length > 0 ? (
              <div style={{ marginTop: "12px" }}>
                <div
                  style={{
                    fontFamily: "'DM Mono', monospace",
                    fontSize: "10px",
                    fontWeight: 600,
                    color: "var(--text-secondary)",
                    letterSpacing: "1px",
                    textTransform: "uppercase",
                    marginBottom: "8px",
                  }}
                >
                  NOTIFICATION STATUS
                </div>
                {Object.entries(alert.notifications).map(([key, value]) => (
                  <div
                    key={key}
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      padding: "6px 10px",
                      background: "var(--surface)",
                      borderRadius: "4px",
                      border: "1px solid var(--line)",
                      marginBottom: "4px",
                    }}
                  >
                    <span
                      style={{
                        fontFamily: "'DM Mono', monospace",
                        fontSize: "11px",
                        color: "var(--text-primary)",
                        textTransform: "capitalize",
                      }}
                    >
                      {key.replace(/_/g, " ")}
                    </span>
                    <span
                      style={{
                        fontFamily: "'DM Mono', monospace",
                        fontSize: "10px",
                        fontWeight: 600,
                        color:
                          value === "NOTIFIED" || value === "WARNING SENT"
                            ? "var(--green)"
                            : value === "PENDING"
                              ? "var(--amber)"
                              : "var(--text-secondary)",
                        textTransform: "uppercase",
                      }}
                    >
                      {String(value)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div
                style={{
                  marginTop: "12px",
                  padding: "12px 14px",
                  background: "var(--surface)",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  color: "var(--text-secondary)",
                  textAlign: "center",
                }}
              >
                No notification data available
              </div>
            )}
          </div>
        </Motion>

        {/* Lifecycle Timeline */}
        <Motion variants={cardReveal}>
          <div className="card" style={{ borderTop: "3px solid var(--accent)", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ marginBottom: "12px" }}>TIMELINE</p>
            <div style={{ display: "grid", gap: "2px" }}>
              <TimelineEntry
                label="Created"
                timestamp={alert.created_at}
                color="var(--text-secondary)"
              />
              <TimelineEntry
                label="Triggered"
                timestamp={alert.triggered_at}
                color="var(--amber)"
              />
              <TimelineEntry
                label="Acknowledged"
                timestamp={alert.acknowledged_at}
                color="var(--amber)"
              />
              <TimelineEntry
                label="Resolved"
                timestamp={alert.resolved_at}
                color="var(--green)"
              />
            </div>
          </div>
        </Motion>
      </Motion>

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

