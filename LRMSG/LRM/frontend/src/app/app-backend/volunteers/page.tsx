"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";
import {
  Users,
  CheckCircle,
  Clock,
  XCircle,
  Pause,
  ArrowRight,
  ServerCrash,
  Search,
  Filter,
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

const STATUS_OPTIONS = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "verified", label: "Verified" },
  { value: "active", label: "Active" },
  { value: "unavailable", label: "Unavailable" },
  { value: "inactive", label: "Inactive" },
];

const STATUS_COLORS: Record<string, string> = {
  pending: "var(--amber)",
  verified: "#3b82f6",
  active: "var(--green)",
  unavailable: "var(--text-secondary)",
  inactive: "var(--red)",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Clock size={12} />,
  verified: <CheckCircle size={12} />,
  active: <CheckCircle size={12} />,
  unavailable: <Pause size={12} />,
  inactive: <XCircle size={12} />,
};

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

function VolunteerCard({
  volunteer,
  onAction,
  actionLoading,
}: {
  volunteer: VolunteerProfile;
  onAction: (id: string, action: string) => void;
  actionLoading: string | null;
}) {
  const isPending = volunteer.status === "pending";
  const isVerified = volunteer.status === "verified";
  const isActive = volunteer.status === "active";
  const isUnavailable = volunteer.status === "unavailable";

  return (
    <Motion variants={cardReveal}>
      <div
        className="card"
        style={{ borderTop: `3px solid ${STATUS_COLORS[volunteer.status] || "var(--line)"}` }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "12px",
          }}
        >
          <StatusBadge status={volunteer.status} />
          <Link
            href={`/app-backend/volunteers/${volunteer.id}`}
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
              fontFamily: "'DM Mono', monospace",
              fontSize: "10px",
              color: "var(--text-secondary)",
              marginBottom: "4px",
            }}
          >
            VOLUNTEER ID
          </div>
          <div
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "13px",
              fontWeight: 600,
              color: "var(--text-primary)",
            }}
          >
            {volunteer.id}
          </div>
        </div>

        {volunteer.skills.length > 0 && (
          <div style={{ marginBottom: "12px" }}>
            <div
              style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: "10px",
                color: "var(--text-secondary)",
                marginBottom: "6px",
              }}
            >
              SKILLS
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
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
          </div>
        )}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: "8px",
            marginBottom: "12px",
          }}
        >
          <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
              TRANSPORT
            </div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
              {volunteer.has_transport === true ? "Yes" : volunteer.has_transport === false ? "No" : "—"}
            </div>
          </div>
          <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
              CAPACITY
            </div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
              {volunteer.capacity != null ? volunteer.capacity : "—"}
            </div>
          </div>
          <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
              ACTIVE
            </div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
              {volunteer.is_active ? "Yes" : "No"}
            </div>
          </div>
        </div>

        {volunteer.availability && (
          <div
            style={{
              padding: "8px 10px",
              background: "var(--surface)",
              borderRadius: "4px",
              marginBottom: "12px",
              fontFamily: "'DM Mono', monospace",
              fontSize: "11px",
              color: "var(--text-secondary)",
            }}
          >
            {volunteer.availability}
          </div>
        )}

        <div
          style={{
            borderTop: "1px solid var(--line)",
            paddingTop: "12px",
            display: "flex",
            gap: "8px",
            flexWrap: "wrap",
          }}
        >
          {isPending && (
            <>
              <button
                onClick={() => onAction(volunteer.id, "verify")}
                disabled={actionLoading === volunteer.id}
                style={{
                  flex: "1 1 auto",
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--green)",
                  background: "var(--green)",
                  color: "#fff",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: actionLoading === volunteer.id ? "not-allowed" : "pointer",
                  opacity: actionLoading === volunteer.id ? 0.6 : 1,
                }}
              >
                {actionLoading === volunteer.id ? "Verifying..." : "Verify"}
              </button>
              <button
                onClick={() => onAction(volunteer.id, "inactive")}
                disabled={actionLoading === volunteer.id}
                style={{
                  flex: "1 1 auto",
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  background: "transparent",
                  color: "var(--text-secondary)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: actionLoading === volunteer.id ? "not-allowed" : "pointer",
                  opacity: actionLoading === volunteer.id ? 0.6 : 1,
                }}
              >
                {actionLoading === volunteer.id ? "Updating..." : "Mark Inactive"}
              </button>
            </>
          )}
          {isVerified && (
            <>
              <button
                onClick={() => onAction(volunteer.id, "active")}
                disabled={actionLoading === volunteer.id}
                style={{
                  flex: "1 1 auto",
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--green)",
                  background: "var(--green)",
                  color: "#fff",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: actionLoading === volunteer.id ? "not-allowed" : "pointer",
                  opacity: actionLoading === volunteer.id ? 0.6 : 1,
                }}
              >
                {actionLoading === volunteer.id ? "Activating..." : "Activate"}
              </button>
              <button
                onClick={() => onAction(volunteer.id, "unavailable")}
                disabled={actionLoading === volunteer.id}
                style={{
                  flex: "1 1 auto",
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  background: "transparent",
                  color: "var(--text-secondary)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: actionLoading === volunteer.id ? "not-allowed" : "pointer",
                  opacity: actionLoading === volunteer.id ? 0.6 : 1,
                }}
              >
                {actionLoading === volunteer.id ? "Updating..." : "Mark Unavailable"}
              </button>
            </>
          )}
          {isActive && (
            <>
              <button
                onClick={() => onAction(volunteer.id, "unavailable")}
                disabled={actionLoading === volunteer.id}
                style={{
                  flex: "1 1 auto",
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  background: "transparent",
                  color: "var(--text-secondary)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: actionLoading === volunteer.id ? "not-allowed" : "pointer",
                  opacity: actionLoading === volunteer.id ? 0.6 : 1,
                }}
              >
                {actionLoading === volunteer.id ? "Updating..." : "Mark Unavailable"}
              </button>
              <button
                onClick={() => onAction(volunteer.id, "inactive")}
                disabled={actionLoading === volunteer.id}
                style={{
                  flex: "1 1 auto",
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  background: "transparent",
                  color: "var(--text-secondary)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: actionLoading === volunteer.id ? "not-allowed" : "pointer",
                  opacity: actionLoading === volunteer.id ? 0.6 : 1,
                }}
              >
                {actionLoading === volunteer.id ? "Updating..." : "Mark Inactive"}
              </button>
            </>
          )}
          {isUnavailable && (
            <>
              <button
                onClick={() => onAction(volunteer.id, "active")}
                disabled={actionLoading === volunteer.id}
                style={{
                  flex: "1 1 auto",
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--green)",
                  background: "var(--green)",
                  color: "#fff",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: actionLoading === volunteer.id ? "not-allowed" : "pointer",
                  opacity: actionLoading === volunteer.id ? 0.6 : 1,
                }}
              >
                {actionLoading === volunteer.id ? "Activating..." : "Activate"}
              </button>
              <button
                onClick={() => onAction(volunteer.id, "inactive")}
                disabled={actionLoading === volunteer.id}
                style={{
                  flex: "1 1 auto",
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  background: "transparent",
                  color: "var(--text-secondary)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: actionLoading === volunteer.id ? "not-allowed" : "pointer",
                  opacity: actionLoading === volunteer.id ? 0.6 : 1,
                }}
              >
                {actionLoading === volunteer.id ? "Updating..." : "Mark Inactive"}
              </button>
            </>
          )}
        </div>
      </div>
    </Motion>
  );
}

export default function VolunteersPage() {
  const [volunteers, setVolunteers] = useState<VolunteerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await apiFetch<VolunteerProfile[]>("/api/volunteers?limit=100");
        if (!cancelled) setVolunteers(data);
      } catch {
        if (!cancelled) setError("Failed to load volunteers");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    let result = volunteers;

    if (statusFilter !== "all") {
      result = result.filter((v) => v.status === statusFilter);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (v) =>
          v.id.toLowerCase().includes(q) ||
          v.user_id.toLowerCase().includes(q) ||
          v.skills.some((s) => s.toLowerCase().includes(q)) ||
          (v.availability && v.availability.toLowerCase().includes(q))
      );
    }

    return result;
  }, [volunteers, statusFilter, searchQuery]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {
      all: volunteers.length,
      pending: 0,
      verified: 0,
      active: 0,
      unavailable: 0,
      inactive: 0,
    };
    for (const v of volunteers) {
      if (counts[v.status] !== undefined) counts[v.status]++;
    }
    return counts;
  }, [volunteers]);

  async function handleAction(id: string, action: string) {
    setActionLoading(id);
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
      setVolunteers((prev) => prev.map((v) => (v.id === id ? updated : v)));
    } catch (e: any) {
      setActionError(e.message || "Action failed");
      setTimeout(() => setActionError(null), 5000);
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Volunteers</h1>
          <p>Loading volunteer data...</p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px" }}>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card" style={{ borderTop: "3px solid var(--line)" }}>
              <div className="skeleton" style={{ width: "60%", height: 12, marginBottom: 12 }} />
              <div className="skeleton" style={{ width: "80%", height: 16, marginBottom: 10 }} />
              <div className="skeleton" style={{ width: "100%", height: 10, marginBottom: 6 }} />
              <div className="skeleton" style={{ width: "40%", height: 10, marginTop: 12 }} />
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
          <h1>Volunteers</h1>
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
        <h1>Volunteers</h1>
        <p>{volunteers.length} total volunteers</p>
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
          <Search size={14} style={{ color: "var(--text-secondary)", flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Search skills, ID, user..."
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
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              style={{
                padding: "6px 12px",
                borderRadius: "4px",
                border: statusFilter === opt.value ? "1px solid var(--accent)" : "1px solid var(--line)",
                background: statusFilter === opt.value ? "var(--accent)" : "transparent",
                color: statusFilter === opt.value ? "#fff" : "var(--text-secondary)",
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
          <Users size={32} style={{ color: "var(--text-secondary)", marginBottom: "12px" }} />
          <div
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "16px",
              fontWeight: 600,
              color: "var(--text-primary)",
              marginBottom: "8px",
            }}
          >
            No volunteers found
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
              : statusFilter !== "all"
                ? `No volunteers in "${statusFilter}" status`
                : "No volunteer profiles have been registered yet"}
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
            {filtered.map((volunteer) => (
              <VolunteerCard
                key={volunteer.id}
                volunteer={volunteer}
                onAction={handleAction}
                actionLoading={actionLoading}
              />
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
        NOTE: Authentication/RBAC is not yet implemented. Volunteer actions are not secured.
      </div>
    </div>
  );
}

