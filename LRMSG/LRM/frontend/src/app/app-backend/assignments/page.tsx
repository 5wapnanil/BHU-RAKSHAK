"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";
import {
  ClipboardList,
  CheckCircle,
  Clock,
  XCircle,
  Pause,
  ArrowRight,
  ServerCrash,
  Search,
  Play,
  Ban,
} from "lucide-react";

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

const STATUS_OPTIONS = [
  { value: "all", label: "All" },
  { value: "pending", label: "Pending" },
  { value: "created", label: "Created" },
  { value: "accepted", label: "Accepted" },
  { value: "in_progress", label: "In Progress" },
  { value: "started", label: "Started" },
  { value: "completed", label: "Completed" },
  { value: "cancelled", label: "Cancelled" },
  { value: "rejected", label: "Rejected" },
];

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

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Clock size={12} />,
  created: <ClipboardList size={12} />,
  accepted: <CheckCircle size={12} />,
  in_progress: <Play size={12} />,
  started: <Play size={12} />,
  completed: <CheckCircle size={12} />,
  cancelled: <Ban size={12} />,
  rejected: <XCircle size={12} />,
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
      {status.replace(/_/g, " ")}
    </span>
  );
}

export default function AssignmentsPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await apiFetch<Assignment[]>("/api/assignments?limit=100");
        if (!cancelled) setAssignments(data);
      } catch {
        if (!cancelled) setError("Failed to load assignments");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    let result = assignments;

    if (statusFilter !== "all") {
      result = result.filter((a) => a.status === statusFilter);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.id.toLowerCase().includes(q) ||
          (a.request_id && a.request_id.toLowerCase().includes(q)) ||
          (a.volunteer_id && a.volunteer_id.toLowerCase().includes(q)) ||
          (a.notes && a.notes.toLowerCase().includes(q))
      );
    }

    return result;
  }, [assignments, statusFilter, searchQuery]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { all: assignments.length };
    for (const opt of STATUS_OPTIONS) {
      if (opt.value !== "all") counts[opt.value] = 0;
    }
    for (const a of assignments) {
      if (counts[a.status] !== undefined) counts[a.status]++;
    }
    return counts;
  }, [assignments]);

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Assignments</h1>
          <p>Loading assignment data...</p>
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
          <h1>Assignments</h1>
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
        <h1>Assignments</h1>
        <p>{assignments.length} total assignments</p>
      </div>

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
            placeholder="Search ID, request, volunteer..."
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
          <ClipboardList size={32} style={{ color: "var(--text-secondary)", marginBottom: "12px" }} />
          <div
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "16px",
              fontWeight: 600,
              color: "var(--text-primary)",
              marginBottom: "8px",
            }}
          >
            No assignments found
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
                ? `No assignments with status "${statusFilter.replace(/_/g, " ")}"`
                : "No assignments have been created yet"}
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
            {filtered.map((assignment) => (
              <Motion key={assignment.id} variants={cardReveal}>
                <div
                  className="card"
                  style={{ borderTop: `3px solid ${STATUS_COLORS[assignment.status] || "var(--line)"}` }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "12px",
                    }}
                  >
                    <StatusBadge status={assignment.status} />
                    <Link
                      href={`/app-backend/assignments/${assignment.id}`}
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
                      ASSIGNMENT ID
                    </div>
                    <div
                      style={{
                        fontFamily: "'Space Grotesk', sans-serif",
                        fontSize: "13px",
                        fontWeight: 600,
                        color: "var(--text-primary)",
                        wordBreak: "break-all",
                      }}
                    >
                      {assignment.id}
                    </div>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "8px",
                      marginBottom: "12px",
                    }}
                  >
                    <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                        TYPE
                      </div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px", textTransform: "capitalize" }}>
                        {assignment.assignment_type}
                      </div>
                    </div>
                    <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                        VOLUNTEER
                      </div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px", wordBreak: "break-all" }}>
                        {assignment.volunteer_id ? assignment.volunteer_id.slice(0, 8) + "..." : "—"}
                      </div>
                    </div>
                  </div>

                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "8px",
                      marginBottom: "12px",
                    }}
                  >
                    <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                        REQUEST
                      </div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px", wordBreak: "break-all" }}>
                        {assignment.request_id ? assignment.request_id.slice(0, 8) + "..." : "—"}
                      </div>
                    </div>
                    <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                        CREATED
                      </div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                        {new Date(assignment.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>

                  {assignment.notes && (
                    <div
                      style={{
                        padding: "8px 10px",
                        background: "var(--surface)",
                        borderRadius: "4px",
                        fontFamily: "'DM Mono', monospace",
                        fontSize: "11px",
                        color: "var(--text-secondary)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {assignment.notes}
                    </div>
                  )}
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
        NOTE: Authentication/RBAC is not yet implemented. Assignment actions are not secured.
      </div>
    </div>
  );
}

