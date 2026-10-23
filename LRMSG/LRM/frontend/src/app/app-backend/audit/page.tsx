"use client";

import { useEffect, useState, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import { AuditEntry } from "@/types/audit";
import { Motion } from "@/components/ui/Motion";
import { fadeInUp } from "@/animations/variants";
import {
  History,
  ServerCrash,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Search,
} from "lucide-react";

const ENTITY_TYPES = [
  "all",
  "volunteer",
  "assignment",
  "resource",
  "request",
  "shelter",
  "alert",
  "incident",
];

const ENTITY_COLORS: Record<string, { bg: string; color: string }> = {
  volunteer: { bg: "#dbeafe", color: "#1e40af" },
  assignment: { bg: "#fef3c7", color: "#92400e" },
  resource: { bg: "#dcfce7", color: "#166534" },
  request: { bg: "#fee2e2", color: "#991b1b" },
  shelter: { bg: "#f3e8ff", color: "#6b21a8" },
  alert: { bg: "#fef3c7", color: "#92400e" },
  incident: { bg: "#fee2e2", color: "#991b1b" },
};

const ACTION_LABELS: Record<string, string> = {
  created: "Created",
  verified: "Verified",
  activated: "Activated",
  status_accepted: "Status: Accepted",
  status_rejected: "Status: Rejected",
  status_in_progress: "Status: In Progress",
  status_completed: "Status: Completed",
  status_cancelled: "Status: Cancelled",
  auto_resolved: "Auto Resolved",
  allocated: "Allocated",
  released: "Released",
  updated: "Updated",
  acknowledged: "Acknowledged",
  under_response: "Under Response",
  resolved: "Resolved",
  active: "Active",
};

const PAGE_SIZE = 25;

function shortenId(id: string): string {
  return id.slice(0, 8);
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  const day = d.getDate();
  const month = d.toLocaleString("en-US", { month: "short" });
  const year = d.getFullYear();
  const hours = d.getHours().toString().padStart(2, "0");
  const minutes = d.getMinutes().toString().padStart(2, "0");
  return `${day} ${month} ${year}, ${hours}:${minutes}`;
}

function JsonBlock({ label, data }: { label: string; data: Record<string, unknown> | null }) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div>
        <div
          style={{
            font: "600 10px 'DM Mono'",
            letterSpacing: "1px",
            color: "var(--text-secondary)",
            marginBottom: "6px",
          }}
        >
          {label}
        </div>
        <div
          style={{
            font: "400 12px 'DM Mono'",
            color: "var(--text-secondary)",
          }}
        >
          None
        </div>
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          font: "600 10px 'DM Mono'",
          letterSpacing: "1px",
          color: "var(--text-secondary)",
          marginBottom: "6px",
        }}
      >
        {label}
      </div>
      <pre
        style={{
          margin: 0,
          padding: "10px 14px",
          background: "var(--paper)",
          borderRadius: "4px",
          border: "1px solid var(--line)",
          font: "400 12px 'DM Mono'",
          color: "var(--text-primary)",
          overflowX: "auto",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
        }}
      >
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [entityFilter, setEntityFilter] = useState("all");
  const [actionFilter, setActionFilter] = useState("");
  const [entityIdSearch, setEntityIdSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(PAGE_SIZE));
      params.set("skip", String(offset));
      if (entityFilter !== "all") params.set("entity_type", entityFilter);
      if (actionFilter.trim()) params.set("action", actionFilter.trim());
      if (entityIdSearch.trim()) params.set("entity_id", entityIdSearch.trim());

      const data = await apiFetch<AuditEntry[]>(`/api/audit-history?${params.toString()}`);
      setEntries(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load audit history");
    } finally {
      setLoading(false);
    }
  }, [offset, entityFilter, actionFilter, entityIdSearch]);

  useEffect(() => {
    fetchEntries();
  }, [fetchEntries]);

  function handleEntityFilter(value: string) {
    setEntityFilter(value);
    setOffset(0);
  }

  function handleActionFilter(value: string) {
    setActionFilter(value);
    setOffset(0);
  }

  function handleEntityIdSearch(value: string) {
    setEntityIdSearch(value);
    setOffset(0);
  }

  function handlePrev() {
    setOffset((o) => Math.max(0, o - PAGE_SIZE));
  }

  function handleNext() {
    setOffset((o) => o + PAGE_SIZE);
  }

  function toggleExpand(id: string) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Audit / History</h1>
          <p>Loading audit records...</p>
        </div>
        <div style={{ display: "grid", gap: "8px" }}>
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              style={{
                display: "flex",
                gap: "16px",
                padding: "14px 0",
                borderBottom: "1px solid var(--line)",
              }}
            >
              <div className="skeleton" style={{ width: "15%", height: 12 }} />
              <div className="skeleton" style={{ width: "10%", height: 12 }} />
              <div className="skeleton" style={{ width: "12%", height: 12 }} />
              <div className="skeleton" style={{ width: "15%", height: 12 }} />
              <div className="skeleton" style={{ width: "10%", height: 12 }} />
              <div className="skeleton" style={{ width: "10%", height: 12 }} />
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
          <h1>Audit / History</h1>
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
          <button
            onClick={fetchEntries}
            style={{
              marginLeft: "auto",
              padding: "6px 14px",
              borderRadius: "4px",
              border: "1px solid #fca5a5",
              background: "#fff",
              color: "#991b1b",
              fontFamily: "'DM Mono', monospace",
              fontSize: "11px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            RETRY
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="analytics-header">
        <h1>Audit / History</h1>
        <p>
          {entries.length > 0
            ? `Showing ${offset + 1}\u2013${Math.min(offset + entries.length, offset + PAGE_SIZE)} of audit records`
            : "Chronological record of system and coordination actions"}
        </p>
      </div>

      <Motion initial="hidden" animate="visible" variants={fadeInUp}>
        {/* Filters */}
        <div
          style={{
            marginBottom: "24px",
            borderRadius: "8px",
            background: "rgba(255,255,255,0.4)",
            backdropFilter: "blur(12px)",
            border: "1px solid var(--line)",
            padding: "16px 20px",
          }}
        >
          <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", alignItems: "center" }}>
            {/* Entity Type Filter */}
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  font: "500 10px 'DM Mono'",
                  letterSpacing: "1px",
                  color: "var(--text-secondary)",
                }}
              >
                ENTITY
              </span>
              {ENTITY_TYPES.map((et) => (
                <button
                  key={et}
                  onClick={() => handleEntityFilter(et)}
                  style={{
                    padding: "5px 10px",
                    borderRadius: "3px",
                    border: "1px solid var(--card-border)",
                    background: entityFilter === et ? "var(--accent)" : "var(--card-bg)",
                    color: entityFilter === et ? "#fff" : "var(--text-secondary)",
                    font: "500 10px 'DM Mono'",
                    letterSpacing: "0.5px",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  {et === "all" ? "ALL" : et.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Action Filter */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                marginLeft: "8px",
              }}
            >
              <span
                style={{
                  font: "500 10px 'DM Mono'",
                  letterSpacing: "1px",
                  color: "var(--text-secondary)",
                }}
              >
                ACTION
              </span>
              <input
                type="text"
                placeholder="e.g. verified"
                value={actionFilter}
                onChange={(e) => handleActionFilter(e.target.value)}
                style={{
                  padding: "5px 10px",
                  borderRadius: "3px",
                  border: "1px solid var(--card-border)",
                  background: "var(--card-bg)",
                  font: "400 11px 'DM Mono'",
                  color: "var(--text-primary)",
                  width: "140px",
                  outline: "none",
                }}
              />
            </div>

            {/* Entity ID Search */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                marginLeft: "8px",
              }}
            >
              <span
                style={{
                  font: "500 10px 'DM Mono'",
                  letterSpacing: "1px",
                  color: "var(--text-secondary)",
                }}
              >
                ENTITY ID
              </span>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "5px 10px",
                  borderRadius: "3px",
                  border: "1px solid var(--card-border)",
                  background: "var(--card-bg)",
                }}
              >
                <Search size={12} style={{ color: "var(--text-secondary)", flexShrink: 0 }} />
                <input
                  type="text"
                  placeholder="UUID"
                  value={entityIdSearch}
                  onChange={(e) => handleEntityIdSearch(e.target.value)}
                  style={{
                    border: "none",
                    background: "transparent",
                    outline: "none",
                    font: "400 11px 'DM Mono'",
                    color: "var(--text-primary)",
                    width: "220px",
                  }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Table */}
        {entries.length === 0 ? (
          <div
            className="card"
            style={{ textAlign: "center", padding: "48px 24px" }}
          >
            <History
              size={32}
              style={{
                color: "var(--text-secondary)",
                opacity: 0.4,
                marginBottom: "16px",
              }}
            />
            <p
              style={{
                font: "600 14px 'Space Grotesk'",
                color: "var(--text-primary)",
                margin: "0 0 8px",
              }}
            >
              No audit records found
            </p>
            <p
              style={{
                font: "400 12px 'DM Sans'",
                color: "var(--text-secondary)",
                margin: 0,
              }}
            >
              {entityFilter !== "all" || actionFilter || entityIdSearch
                ? "No audit records match the selected filters."
                : "No audit records have been generated yet."}
            </p>
            {(entityFilter !== "all" || actionFilter || entityIdSearch) && (
              <button
                onClick={() => {
                  setEntityFilter("all");
                  setActionFilter("");
                  setEntityIdSearch("");
                  setOffset(0);
                }}
                style={{
                  marginTop: "16px",
                  padding: "8px 16px",
                  borderRadius: "4px",
                  border: "1px solid var(--card-border)",
                  background: "var(--card-bg)",
                  color: "var(--accent)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                CLEAR FILTERS
              </button>
            )}
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontFamily: "'DM Sans', sans-serif",
                fontSize: "13px",
              }}
            >
              <thead>
                <tr style={{ borderBottom: "2px solid var(--line)" }}>
                  {["TIMESTAMP", "ENTITY", "ENTITY ID", "ACTION", "ACTOR", "CHANGES"].map(
                    (h) => (
                      <th
                        key={h}
                        style={{
                          textAlign: "left",
                          padding: "12px 14px",
                          font: "600 10px 'DM Mono'",
                          color: "var(--text-secondary)",
                          letterSpacing: "1px",
                        }}
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => {
                  const entityColor = ENTITY_COLORS[entry.entity_type] || {
                    bg: "#f3f4f6",
                    color: "#374151",
                  };
                  const actionLabel =
                    ACTION_LABELS[entry.action] ||
                    entry.action
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (c) => c.toUpperCase());
                  const isExpanded = expandedId === entry.id;
                  const hasChanges =
                    entry.old_value !== null || entry.new_value !== null;

                  return (
                    <tr
                      key={entry.id}
                      style={{
                        borderBottom: "1px solid var(--line)",
                        transition: "background 0.15s",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.background = "var(--surface)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.background = "transparent")
                      }
                    >
                      <td
                        style={{
                          padding: "12px 14px",
                          color: "var(--text-secondary)",
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "11px",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {formatTimestamp(entry.created_at)}
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        <span
                          style={{
                            display: "inline-block",
                            padding: "3px 8px",
                            borderRadius: "2px",
                            font: "700 10px 'DM Mono'",
                            letterSpacing: "0.5px",
                            background: entityColor.bg,
                            color: entityColor.color,
                          }}
                        >
                          {entry.entity_type.toUpperCase()}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: "12px 14px",
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "11px",
                          color: "var(--text-secondary)",
                        }}
                        title={entry.entity_id}
                      >
                        {shortenId(entry.entity_id)}
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        <span
                          style={{
                            font: "600 11px 'DM Mono'",
                            color: "var(--text-primary)",
                          }}
                        >
                          {actionLabel}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: "12px 14px",
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "11px",
                          color: entry.actor_id
                            ? "var(--text-primary)"
                            : "var(--text-secondary)",
                        }}
                        title={entry.actor_id || undefined}
                      >
                        {entry.actor_id
                          ? shortenId(entry.actor_id)
                          : "System"}
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        {hasChanges ? (
                          <button
                            onClick={() => toggleExpand(entry.id)}
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              padding: "4px 10px",
                              borderRadius: "3px",
                              border: "1px solid var(--card-border)",
                              background: isExpanded
                                ? "var(--accent)"
                                : "var(--card-bg)",
                              color: isExpanded
                                ? "#fff"
                                : "var(--accent)",
                              font: "600 10px 'DM Mono'",
                              letterSpacing: "0.5px",
                              cursor: "pointer",
                              transition: "all 0.15s ease",
                            }}
                          >
                            {isExpanded ? (
                              <>
                                HIDE <ChevronUp size={12} />
                              </>
                            ) : (
                              <>
                                VIEW <ChevronDown size={12} />
                              </>
                            )}
                          </button>
                        ) : (
                          <span
                            style={{
                              font: "400 11px 'DM Mono'",
                              color: "var(--text-secondary)",
                            }}
                          >
                            \u2014
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Expanded details rendered below the table row */}
            {expandedId &&
              entries
                .filter((e) => e.id === expandedId)
                .map((entry) => (
                  <div
                    key={`detail-${entry.id}`}
                    style={{
                      padding: "16px 20px",
                      borderBottom: "2px solid var(--line)",
                      background: "var(--surface)",
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: "20px",
                    }}
                  >
                    <JsonBlock label="OLD VALUE" data={entry.old_value} />
                    <JsonBlock label="NEW VALUE" data={entry.new_value} />
                  </div>
                ))}

            {/* Pagination */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "16px 14px",
                borderTop: "1px solid var(--line)",
              }}
            >
              <span
                style={{
                  font: "500 11px 'DM Mono'",
                  color: "var(--text-secondary)",
                }}
              >
                {entries.length} record{entries.length !== 1 ? "s" : ""} on this
                page
              </span>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  onClick={handlePrev}
                  disabled={offset === 0}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    padding: "6px 12px",
                    borderRadius: "3px",
                    border: "1px solid var(--card-border)",
                    background: offset === 0 ? "var(--surface)" : "var(--card-bg)",
                    color: offset === 0 ? "var(--text-secondary)" : "var(--text-primary)",
                    font: "600 10px 'DM Mono'",
                    letterSpacing: "0.5px",
                    cursor: offset === 0 ? "default" : "pointer",
                    opacity: offset === 0 ? 0.5 : 1,
                    transition: "all 0.15s ease",
                  }}
                >
                  <ChevronLeft size={14} /> PREV
                </button>
                <button
                  onClick={handleNext}
                  disabled={entries.length < PAGE_SIZE}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "4px",
                    padding: "6px 12px",
                    borderRadius: "3px",
                    border: "1px solid var(--card-border)",
                    background:
                      entries.length < PAGE_SIZE
                        ? "var(--surface)"
                        : "var(--card-bg)",
                    color:
                      entries.length < PAGE_SIZE
                        ? "var(--text-secondary)"
                        : "var(--text-primary)",
                    font: "600 10px 'DM Mono'",
                    letterSpacing: "0.5px",
                    cursor: entries.length < PAGE_SIZE ? "default" : "pointer",
                    opacity: entries.length < PAGE_SIZE ? 0.5 : 1,
                    transition: "all 0.15s ease",
                  }}
                >
                  NEXT <ChevronRight size={14} />
                </button>
              </div>
            </div>
          </div>
        )}
      </Motion>
    </div>
  );
}
