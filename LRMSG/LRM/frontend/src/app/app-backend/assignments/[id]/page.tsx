"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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
  Play,
  Ban,
  ServerCrash,
  ClipboardList,
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Assignment {
  id: string;
  request_id: string | null;
  volunteer_id: string | null;
  resource_id: string | null;
  assignment_type: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "var(--amber)",
  created: "#3b82f6",
  accepted: "#8b5cf6",
  in_progress: "var(--green)",
  started: "#3b82f6",
  completed: "var(--green)",
  cancelled: "var(--text-secondary)",
  rejected: "var(--red)",
};

const VALID_TRANSITIONS: Record<string, string[]> = {
  pending: ["accepted", "rejected", "cancelled"],
  created: ["accepted", "cancelled"],
  accepted: ["started", "in_progress", "cancelled"],
  rejected: [],
  started: ["completed", "cancelled"],
  in_progress: ["completed", "cancelled"],
  completed: [],
  cancelled: [],
};

const ACTION_LABELS: Record<string, string> = {
  accepted: "Accept",
  rejected: "Reject",
  cancelled: "Cancel",
  started: "Start",
  in_progress: "Start",
  completed: "Complete",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "var(--text-secondary)";
  const iconMap: Record<string, React.ReactNode> = {
    pending: <Clock size={12} />,
    created: <ClipboardList size={12} />,
    accepted: <CheckCircle size={12} />,
    in_progress: <Play size={12} />,
    started: <Play size={12} />,
    completed: <CheckCircle size={12} />,
    cancelled: <Ban size={12} />,
    rejected: <XCircle size={12} />,
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
      {status.replace(/_/g, " ")}
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
          wordBreak: "break-all",
        }}
      >
        {value}
      </span>
    </div>
  );
}

export default function AssignmentDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await apiFetch<Assignment>(`/api/assignments/${id}`);
        if (!cancelled) setAssignment(data);
      } catch {
        if (!cancelled) setError("Failed to load assignment");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [id]);

  async function handleAction(newStatus: string) {
    setActionLoading(true);
    setActionError(null);

    try {
      const res = await fetch(`${API}/api/assignments/${id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(detail?.detail || `Action failed (${res.status})`);
      }

      const updated: Assignment = await res.json();
      setAssignment(updated);
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
        <Link
          href="/app-backend/assignments"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            font: "600 11px 'DM Mono'",
            color: "var(--text-secondary)",
            textDecoration: "none",
            marginBottom: "24px",
            letterSpacing: "0.5px",
          }}
        >
          <ArrowLeft size={14} /> BACK TO ASSIGNMENTS
        </Link>
        <div className="analytics-header">
          <h1>Loading assignment...</h1>
        </div>
        <div style={{ display: "grid", gap: "16px" }}>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card">
              <div className="skeleton" style={{ width: "40%", height: 12, marginBottom: 12 }} />
              <div className="skeleton" style={{ width: "80%", height: 16 }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !assignment) {
    return (
      <div>
        <Link
          href="/app-backend/assignments"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            font: "600 11px 'DM Mono'",
            color: "var(--text-secondary)",
            textDecoration: "none",
            marginBottom: "24px",
            letterSpacing: "0.5px",
          }}
        >
          <ArrowLeft size={14} /> BACK TO ASSIGNMENTS
        </Link>
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
          {error || "Assignment not found"}
        </div>
      </div>
    );
  }

  const allowedActions = VALID_TRANSITIONS[assignment.status] || [];
  const isTerminal = allowedActions.length === 0;

  return (
    <div>
      <div className="analytics-header">
        <Link
          href="/app-backend/assignments"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            font: "600 11px 'DM Mono'",
            color: "var(--text-secondary)",
            textDecoration: "none",
            marginBottom: "16px",
            letterSpacing: "0.5px",
          }}
        >
          <ArrowLeft size={14} /> BACK TO ASSIGNMENTS
        </Link>
        <h1>Assignment Detail</h1>
        <p>Manage assignment status and view details</p>
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
          <StatusBadge status={assignment.status} />
          <span
            style={{
              padding: "4px 10px",
              borderRadius: "12px",
              fontFamily: "'DM Mono', monospace",
              fontSize: "10px",
              fontWeight: 600,
              color: "var(--text-secondary)",
              background: "var(--surface)",
              border: "1px solid var(--line)",
              textTransform: "uppercase",
            }}
          >
            {assignment.assignment_type}
          </span>
        </div>

        <div className="card" style={{ marginBottom: "16px" }}>
          <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ margin: 0 }}>ASSIGNMENT INFORMATION</p>
          </div>
          <div style={{ display: "grid", gap: "8px" }}>
            <DetailRow label="Assignment ID" value={assignment.id} />
            <DetailRow label="Type" value={assignment.assignment_type} />
            <DetailRow label="Request ID" value={assignment.request_id || "—"} />
            <DetailRow label="Volunteer ID" value={assignment.volunteer_id || "—"} />
            <DetailRow label="Resource ID" value={assignment.resource_id || "—"} />
            <DetailRow label="Notes" value={assignment.notes || "—"} />
          </div>
        </div>

        <div className="card" style={{ marginBottom: "16px" }}>
          <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ margin: 0 }}>TIMESTAMPS</p>
          </div>
          <div style={{ display: "grid", gap: "8px" }}>
            <DetailRow
              label="Created At"
              value={new Date(assignment.created_at).toLocaleString()}
            />
            <DetailRow
              label="Updated At"
              value={new Date(assignment.updated_at).toLocaleString()}
            />
          </div>
        </div>

        {!isTerminal && (
          <div className="card">
            <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
              <p className="eyebrow" style={{ margin: 0 }}>ACTIONS</p>
            </div>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              {allowedActions.map((action) => {
                const isDestructive = action === "cancelled" || action === "rejected";
                return (
                  <button
                    key={action}
                    onClick={() => handleAction(action)}
                    disabled={actionLoading}
                    style={{
                      padding: "8px 20px",
                      borderRadius: "4px",
                      border: isDestructive ? "1px solid var(--line)" : "1px solid var(--green)",
                      background: isDestructive ? "transparent" : "var(--green)",
                      color: isDestructive ? "var(--text-secondary)" : "#fff",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: actionLoading ? "not-allowed" : "pointer",
                      opacity: actionLoading ? 0.6 : 1,
                    }}
                  >
                    {actionLoading ? "Processing..." : ACTION_LABELS[action] || action}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {isTerminal && (
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
              This assignment is in a terminal state ({assignment.status}). No further status transitions are available.
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
        NOTE: Authentication/RBAC is not yet implemented. Assignment actions are not secured.
      </div>
    </div>
  );
}

