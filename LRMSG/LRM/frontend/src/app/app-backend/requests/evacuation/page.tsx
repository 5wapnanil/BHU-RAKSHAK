"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { EmergencyRequest } from "@/types/coordination";
import { Motion } from "@/components/ui/Motion";
import { fadeInUp, staggerContainer } from "@/animations/variants";
import { Car, ServerCrash, ExternalLink, Phone, ArrowDownUp } from "lucide-react";

const STATUS_STYLES: Record<string, { bg: string; color: string }> = {
  pending: { bg: "#fef3c7", color: "#92400e" },
  in_progress: { bg: "#dbeafe", color: "#1e40af" },
  resolved: { bg: "#dcfce7", color: "#166534" },
  cancelled: { bg: "#f3f4f6", color: "#374151" },
};

const SERVER_STATUS_STYLES: Record<string, { bg: string; color: string }> = {
  received: { bg: "#fef3c7", color: "#92400e" },
  processing: { bg: "#dbeafe", color: "#1e40af" },
  synced: { bg: "#dcfce7", color: "#166534" },
  failed: { bg: "#fee2e2", color: "#991b1b" },
};

const SEVERITY_STYLES: Record<string, { bg: string; color: string }> = {
  high: { bg: "#fee2e2", color: "#991b1b" },
  critical: { bg: "#dc2626", color: "#ffffff" },
  moderate: { bg: "#fef3c7", color: "#92400e" },
  low: { bg: "#dcfce7", color: "#166534" },
};

function Badge({ label, style }: { label: string; style: { bg: string; color: string } }) {
  return (
    <span
      style={{
        display: "inline-block",
        padding: "3px 8px",
        borderRadius: "2px",
        font: "700 10px 'DM Mono'",
        letterSpacing: "0.5px",
        background: style.bg,
        color: style.color,
      }}
    >
      {label}
    </span>
  );
}

const EVACUATION_TYPES = new Set(["evacuation"]);

function isEvacuationRequest(r: EmergencyRequest) {
  return EVACUATION_TYPES.has(r.request_type);
}

const SEVERITY_RANK: Record<string, number> = {
  critical: 0,
  high: 1,
  moderate: 2,
  low: 3,
};

type SortOption = "newest" | "name" | "severity";

function sortRequests(requests: EmergencyRequest[], sortBy: SortOption): EmergencyRequest[] {
  const sorted = [...requests];
  switch (sortBy) {
    case "newest":
      return sorted.sort((a, b) => {
        const da = a.created_at ? new Date(a.created_at).getTime() : 0;
        const db = b.created_at ? new Date(b.created_at).getTime() : 0;
        return db - da;
      });
    case "name":
      return sorted.sort((a, b) => {
        const na = (a.contact_name || "").toLowerCase();
        const nb = (b.contact_name || "").toLowerCase();
        if (!na && !nb) return 0;
        if (!na) return 1;
        if (!nb) return -1;
        return na.localeCompare(nb);
      });
    case "severity":
      return sorted.sort((a, b) => {
        const ra = a.severity ? (SEVERITY_RANK[a.severity.toLowerCase()] ?? 4) : 4;
        const rb = b.severity ? (SEVERITY_RANK[b.severity.toLowerCase()] ?? 4) : 4;
        return ra - rb;
      });
  }
}

export default function EvacuationRequestsPage() {
  const [requests, setRequests] = useState<EmergencyRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<SortOption>("newest");

  useEffect(() => {
    apiFetch<EmergencyRequest[]>("/api/requests?limit=200")
      .then((data) => setRequests(data.filter(isEvacuationRequest)))
      .catch(() => setError("Failed to load Evacuation Requests"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === "all" ? requests : requests.filter((r) => r.status === filter);

  const sorted = useMemo(() => sortRequests(filtered, sortBy), [filtered, sortBy]);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: requests.length, pending: 0, in_progress: 0, resolved: 0, cancelled: 0 };
    for (const r of requests) {
      if (c[r.status] !== undefined) c[r.status]++;
    }
    return c;
  }, [requests]);

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Evacuation Requests</h1>
          <p>Loading Evacuation Requests...</p>
        </div>
        <div style={{ display: "grid", gap: "8px" }}>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} style={{ display: "flex", gap: "16px", padding: "14px 0", borderBottom: "1px solid var(--line)" }}>
              <div className="skeleton" style={{ width: "15%", height: 12 }} />
              <div className="skeleton" style={{ width: "10%", height: 12 }} />
              <div className="skeleton" style={{ width: "10%", height: 12 }} />
              <div className="skeleton" style={{ width: "20%", height: 12 }} />
              <div className="skeleton" style={{ width: "15%", height: 12 }} />
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
          <h1>Evacuation Requests</h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "24px", background: "#fee2e2", borderRadius: "8px", border: "1px solid #fca5a5", fontFamily: "'DM Mono', monospace", fontSize: "13px", color: "#991b1b" }}>
          <ServerCrash size={20} /> {error}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="analytics-header">
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
          <Car size={20} style={{ color: "var(--green)" }} />
          <h1 style={{ margin: 0 }}>Evacuation Requests</h1>
        </div>
        <p>{requests.length} relief request{requests.length !== 1 ? "s" : ""} from the database</p>
      </div>

      <Motion initial="hidden" animate="visible" variants={fadeInUp}>
        <div className="filter-bar" style={{ marginBottom: "24px", borderRadius: "8px", background: "rgba(255,255,255,0.4)", backdropFilter: "blur(12px)", border: "1px solid var(--line)", padding: "16px 20px" }}>
          <span style={{ font: "500 10px 'DM Mono'", letterSpacing: "1px", color: "var(--text-secondary)" }}>FILTER</span>
          {["all", "pending", "in_progress", "resolved", "cancelled"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: "6px 12px",
                borderRadius: "3px",
                border: "1px solid var(--card-border)",
                background: filter === f ? "var(--accent)" : "var(--card-bg)",
                color: filter === f ? "#fff" : "var(--text-secondary)",
                font: "500 10px 'DM Mono'",
                letterSpacing: "0.5px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {f === "all" ? "ALL" : f.toUpperCase().replace("_", " ")} ({counts[f] ?? 0})
            </button>
          ))}
          <span style={{ marginLeft: "auto", font: "500 10px 'DM Mono'", letterSpacing: "1px", color: "var(--text-secondary)", display: "inline-flex", alignItems: "center", gap: "6px" }}>
            <ArrowDownUp size={12} />
            <span>SORT BY</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              style={{
                padding: "4px 8px",
                borderRadius: "3px",
                border: "1px solid var(--card-border)",
                background: "var(--card-bg)",
                color: "var(--text-primary)",
                font: "500 10px 'DM Mono'",
                letterSpacing: "0.5px",
                cursor: "pointer",
                outline: "none",
              }}
            >
              <option value="newest">Newest</option>
              <option value="name">Name</option>
              <option value="severity">Severity</option>
            </select>
          </span>
          <span style={{ font: "500 10px 'DM Mono'", letterSpacing: "1px", color: "var(--text-secondary)" }}>
            {sorted.length} SHOWN
          </span>
        </div>
      </Motion>

      {sorted.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "48px 24px" }}>
          <Car size={32} style={{ color: "var(--text-secondary)", opacity: 0.4, marginBottom: "16px" }} />
          <p style={{ font: "600 14px 'Space Grotesk'", color: "var(--text-primary)", margin: "0 0 8px" }}>
            No Evacuation Requests found
          </p>
          <p style={{ font: "400 12px 'DM Sans'", color: "var(--text-secondary)", margin: 0 }}>
            {filter === "all"
              ? "Evacuation Requests submitted from the mobile app will appear here."
              : `No Evacuation Requests with status "${filter.replace("_", " ")}".`}
          </p>
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
                <th style={{ textAlign: "left", padding: "12px 14px", font: "600 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}>STATUS</th>
                <th style={{ textAlign: "left", padding: "12px 14px", font: "600 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}>SERVER</th>
                <th style={{ textAlign: "left", padding: "12px 14px", font: "600 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}>SEVERITY</th>
                <th style={{ textAlign: "left", padding: "12px 14px", font: "600 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}>LOCATION</th>
                <th style={{ textAlign: "left", padding: "12px 14px", font: "600 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}>REQUESTER</th>
                <th style={{ textAlign: "left", padding: "12px 14px", font: "600 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}>PEOPLE</th>
                <th style={{ textAlign: "left", padding: "12px 14px", font: "600 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}>CREATED</th>
                <th style={{ textAlign: "left", padding: "12px 14px", font: "600 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}></th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((req) => (
                <tr
                  key={req.id}
                  style={{ borderBottom: "1px solid var(--line)", transition: "background 0.15s" }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <td style={{ padding: "12px 14px" }}>
                    <Badge
                      label={req.status.replace(/_/g, " ")}
                      style={STATUS_STYLES[req.status] || { bg: "#f3f4f6", color: "#374151" }}
                    />
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    {req.server_status && (
                      <Badge
                        label={req.server_status}
                        style={SERVER_STATUS_STYLES[req.server_status] || { bg: "#f3f4f6", color: "#374151" }}
                      />
                    )}
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    {req.severity && (
                      <Badge
                        label={req.severity}
                        style={SEVERITY_STYLES[req.severity] || { bg: "#f3f4f6", color: "#374151" }}
                      />
                    )}
                  </td>
                  <td style={{ padding: "12px 14px", color: "var(--text-secondary)", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {req.location_text || "â€”"}
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    {req.contact_name ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                        <span style={{ font: "600 12px 'DM Sans'", color: "var(--text-primary)" }}>{req.contact_name}</span>
                        {req.contact_phone && (
                          <a
                            href={`tel:${req.contact_phone}`}
                            style={{ font: "500 11px 'DM Mono'", color: "var(--accent-text)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px" }}
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Phone size={10} /> {req.contact_phone}
                          </a>
                        )}
                      </div>
                    ) : "â€”"}
                  </td>
                  <td style={{ padding: "12px 14px", textAlign: "center" }}>
                    {req.people_affected != null ? req.people_affected : "â€”"}
                  </td>
                  <td style={{ padding: "12px 14px", color: "var(--text-secondary)", fontFamily: "'DM Mono', monospace", fontSize: "11px" }}>
                    {req.created_at ? new Date(req.created_at).toLocaleDateString() : "â€”"}
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    <Link
                      href={`/app-backend/requests/${req.id}`}
                      style={{ color: "var(--accent-text)", textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "4px", font: "600 10px 'DM Mono'", letterSpacing: "0.5px" }}
                    >
                      VIEW <ExternalLink size={12} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


