"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";
import {
  ArrowLeft,
  CheckCircle,
  Clock,
  XCircle,
  Pause,
  ServerCrash,
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface VolunteerProfile {
  id: string;
  user_id: string;
  skills: string[];
  has_transport: boolean | null;
  capacity: number | null;
  availability: string | null;
  status: string;
  is_active: boolean;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "var(--amber)",
  verified: "#3b82f6",
  active: "var(--green)",
  unavailable: "var(--text-secondary)",
  inactive: "var(--red)",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "var(--text-secondary)";
  const iconMap: Record<string, React.ReactNode> = {
    pending: <Clock size={12} />,
    verified: <CheckCircle size={12} />,
    active: <CheckCircle size={12} />,
    unavailable: <Pause size={12} />,
    inactive: <XCircle size={12} />,
  };
  return (
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
        color,
        background: `${color}15`,
        border: `1px solid ${color}30`,
        textTransform: "uppercase",
      }}
    >
      {iconMap[status] || null}
      {status}
    </span>
  );
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "12px 14px",
        background: "var(--surface)",
        borderRadius: "4px",
        border: "1px solid var(--line)",
      }}
    >
      <span
        style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: "12px",
          fontWeight: 600,
          color: "var(--text-primary)",
        }}
      >
        {label}
      </span>
      <span
        style={{
          fontFamily: "'DM Mono', monospace",
          fontSize: "12px",
          color: "var(--text-secondary)",
          textAlign: "right",
        }}
      >
        {value}
      </span>
    </div>
  );
}

export default function VolunteerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [volunteer, setVolunteer] = useState<VolunteerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await apiFetch<VolunteerProfile>(`/api/volunteers/${id}`);
        if (!cancelled) setVolunteer(data);
      } catch {
        if (!cancelled) setError("Failed to load volunteer");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [id]);

  async function handleAction(action: string) {
    setActionLoading(true);
    setActionError(null);

    let url: string;
    let method: string;
    let body: string | undefined;

    if (action === "verify") {
      url = `${API}/api/volunteers/${id}/verify`;
      method = "POST";
    } else if (action === "active") {
      url = `${API}/api/volunteers/${id}/activate`;
      method = "POST";
    } else {
      url = `${API}/api/volunteers/${id}/status`;
      method = "PATCH";
      body = JSON.stringify({ status: action });
    }

    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body,
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(detail?.detail || `Action failed (${res.status})`);
      }

      const updated: VolunteerProfile = await res.json();
      setVolunteer(updated);
    } catch (e: any) {
      setActionError(e.message || "Action failed");
      setTimeout(() => setActionError(null), 5000);
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <Link
            href="/app-backend/volunteers"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontFamily: "'DM Mono', monospace",
              fontSize: "12px",
              color: "var(--text-secondary)",
              textDecoration: "none",
              marginBottom: "16px",
            }}
          >
            <ArrowLeft size={14} />
            Back to Volunteers
          </Link>
          <h1>Volunteer Detail</h1>
          <p>Loading...</p>
        </div>
        <div style={{ display: "grid", gap: "12px" }}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="skeleton" style={{ height: 48, borderRadius: "4px" }} />
          ))}
        </div>
      </div>
    );
  }

  if (error || !volunteer) {
    return (
      <div>
        <div className="analytics-header">
          <Link
            href="/app-backend/volunteers"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontFamily: "'DM Mono', monospace",
              fontSize: "12px",
              color: "var(--text-secondary)",
              textDecoration: "none",
              marginBottom: "16px",
            }}
          >
            <ArrowLeft size={14} />
            Back to Volunteers
          </Link>
          <h1>Volunteer Detail</h1>
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
          {error || "Volunteer not found"}
        </div>
      </div>
    );
  }

  const isPending = volunteer.status === "pending";
  const isVerified = volunteer.status === "verified";
  const isActive = volunteer.status === "active";
  const isUnavailable = volunteer.status === "unavailable";

  return (
    <div>
      <div className="analytics-header">
        <Link
          href="/app-backend/volunteers"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            fontFamily: "'DM Mono', monospace",
            fontSize: "12px",
            color: "var(--text-secondary)",
            textDecoration: "none",
            marginBottom: "16px",
          }}
        >
          <ArrowLeft size={14} />
          Back to Volunteers
        </Link>
        <h1>Volunteer Detail</h1>
        <p>Manage volunteer profile and status</p>
      </div>

      {actionError && (
        <div
          style={{
            padding: "12px 16px",
            marginBottom: "16px",
            background: "#fee2e2",
            borderRadius: "6px",
            border: "1px solid #fca5a5",
            fontFamily: "'DM Mono', monospace",
            fontSize: "12px",
            color: "#991b1b",
          }}
        >
          {actionError}
        </div>
      )}

      <Motion initial="hidden" animate="visible" variants={staggerContainer}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
          <StatusBadge status={volunteer.status} />
          {volunteer.is_active && (
            <span
              style={{
                padding: "4px 10px",
                borderRadius: "12px",
                fontFamily: "'DM Mono', monospace",
                fontSize: "10px",
                fontWeight: 600,
                color: "var(--green)",
                background: "var(--green)15",
                border: "1px solid var(--green)30",
                textTransform: "uppercase",
              }}
            >
              Active Profile
            </span>
          )}
        </div>

        <div className="card" style={{ marginBottom: "16px" }}>
          <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ margin: 0 }}>PROFILE INFORMATION</p>
          </div>
          <div style={{ display: "grid", gap: "8px" }}>
            <DetailRow label="Volunteer ID" value={volunteer.id} />
            <DetailRow label="User ID" value={volunteer.user_id} />
            <DetailRow
              label="Skills"
              value={
                volunteer.skills.length > 0 ? (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", justifyContent: "flex-end" }}>
                    {volunteer.skills.map((skill) => (
                      <span
                        key={skill}
                        style={{
                          padding: "2px 8px",
                          borderRadius: "4px",
                          background: "var(--surface)",
                          border: "1px solid var(--line)",
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "10px",
                          color: "var(--text-primary)",
                        }}
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  "—"
                )
              }
            />
            <DetailRow
              label="Transport"
              value={volunteer.has_transport === true ? "Yes" : volunteer.has_transport === false ? "No" : "—"}
            />
            <DetailRow label="Capacity" value={volunteer.capacity != null ? String(volunteer.capacity) : "—"} />
            <DetailRow label="Availability" value={volunteer.availability || "—"} />
          </div>
        </div>

        <div className="card" style={{ marginBottom: "16px" }}>
          <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ margin: 0 }}>TIMESTAMPS</p>
          </div>
          <div style={{ display: "grid", gap: "8px" }}>
            <DetailRow
              label="Verified At"
              value={volunteer.verified_at ? new Date(volunteer.verified_at).toLocaleString() : "—"}
            />
            <DetailRow
              label="Created At"
              value={new Date(volunteer.created_at).toLocaleString()}
            />
            <DetailRow
              label="Updated At"
              value={new Date(volunteer.updated_at).toLocaleString()}
            />
          </div>
        </div>

        {(isPending || isVerified || isActive || isUnavailable) && (
          <div className="card">
            <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
              <p className="eyebrow" style={{ margin: 0 }}>ACTIONS</p>
            </div>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              {isPending && (
                <>
                  <button
                    onClick={() => handleAction("verify")}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: "1px solid var(--green)",
                      background: "var(--green)",
                      color: "#fff",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : "Verify Volunteer"}
                  </button>
                  <button
                    onClick={() => handleAction("inactive")}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: "1px solid var(--line)",
                      background: "transparent",
                      color: "var(--text-secondary)",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : "Mark Inactive"}
                  </button>
                </>
              )}
              {isVerified && (
                <>
                  <button
                    onClick={() => handleAction("active")}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: "1px solid var(--green)",
                      background: "var(--green)",
                      color: "#fff",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : "Activate Volunteer"}
                  </button>
                  <button
                    onClick={() => handleAction("unavailable")}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: "1px solid var(--line)",
                      background: "transparent",
                      color: "var(--text-secondary)",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : "Mark Unavailable"}
                  </button>
                  <button
                    onClick={() => handleAction("inactive")}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: "1px solid var(--line)",
                      background: "transparent",
                      color: "var(--text-secondary)",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : "Mark Inactive"}
                  </button>
                </>
              )}
              {isActive && (
                <>
                  <button
                    onClick={() => handleAction("unavailable")}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: "1px solid var(--line)",
                      background: "transparent",
                      color: "var(--text-secondary)",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : "Mark Unavailable"}
                  </button>
                  <button
                    onClick={() => handleAction("inactive")}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: "1px solid var(--line)",
                      background: "transparent",
                      color: "var(--text-secondary)",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : "Mark Inactive"}
                  </button>
                </>
              )}
              {isUnavailable && (
                <>
                  <button
                    onClick={() => handleAction("active")}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: "1px solid var(--green)",
                      background: "var(--green)",
                      color: "#fff",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : "Activate Volunteer"}
                  </button>
                  <button
                    onClick={() => handleAction("inactive")}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: "1px solid var(--line)",
                      background: "transparent",
                      color: "var(--text-secondary)",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : "Mark Inactive"}
                  </button>
                </>
              )}
            </div>
          </div>
        )}

        {volunteer.status === "inactive" && (
          <div className="card">
            <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
              <p className="eyebrow" style={{ margin: 0 }}>ACTIONS</p>
            </div>
            <div
              style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: "12px",
                color: "var(--text-secondary)",
              }}
            >
              This volunteer is inactive. No further status transitions are available.
              To re-enable, a new volunteer profile must be registered.
            </div>
          </div>
        )}
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
        NOTE: Authentication/RBAC is not yet implemented. Volunteer actions are not secured.
      </div>
    </div>
  );
}

