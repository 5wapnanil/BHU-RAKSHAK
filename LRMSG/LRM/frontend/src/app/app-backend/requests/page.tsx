"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { EmergencyRequest } from "@/types/coordination";
import { Motion } from "@/components/ui/Motion";
import { fadeInUp, staggerContainer } from "@/animations/variants";
import { Siren, MapPin, Clock, Users, ServerCrash, ExternalLink, Phone } from "lucide-react";

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

export default function RequestsPage() {
  const [requests, setRequests] = useState<EmergencyRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    apiFetch<EmergencyRequest[]>("/api/requests?limit=100")
      .then((data) => setRequests(data))
      .catch(() => setError("Failed to load emergency requests"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === "all" ? requests : requests.filter((r) => r.status === filter);

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Emergency Requests</h1>
          <p>Loading requests...</p>
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
          <h1>Emergency Requests</h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "24px", background: "#fee2e2", borderRadius: "8px", border: "1px solid #fca5a5", fontFamily: "'DM Mono', monospace", fontSize: "13px", color: "#991b1b" }}>
          <ServerCrash size={20} />
          {error}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="analytics-header">
        <h1>Emergency Requests</h1>
        <p>{requests.length} total request{requests.length !== 1 ? "s" : ""} from the database</p>
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
              {f === "all" ? "ALL" : f.toUpperCase().replace("_", " ")}
            </button>
          ))}
          <span style={{ marginLeft: "auto", font: "500 10px 'DM Mono'", letterSpacing: "1px", color: "var(--text-secondary)" }}>
            {filtered.length} SHOWN
          </span>
        </div>
      </Motion>

      {filtered.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "48px 24px" }}>
          <Siren size={32} style={{ color: "var(--text-secondary)", opacity: 0.4, marginBottom: "16px" }} />
          <p style={{ font: "600 14px 'Space Grotesk'", color: "var(--text-primary)", margin: "0 0 8px" }}>
            No requests found
          </p>
          <p style={{ font: "400 12px 'DM Sans'", color: "var(--text-secondary)", margin: 0 }}>
            {filter === "all"
              ? "Emergency requests submitted from the mobile app will appear here."
              : `No requests with status "${filter.replace("_", " ")}".`}
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
                <th style={{ textAlign: "left", padding: "12px 14px", font: "600 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}>TYPE</th>
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
              {filtered.map((req) => (
                <tr
                  key={req.id}
                  style={{ borderBottom: "1px solid var(--line)", transition: "background 0.15s" }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <td style={{ padding: "12px 14px", fontWeight: 600, textTransform: "capitalize" }}>
                    {req.request_type.replace(/_/g, " ")}
                  </td>
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
                    {req.location_text || "—"}
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
                    ) : "—"}
                  </td>
                  <td style={{ padding: "12px 14px", textAlign: "center" }}>
                    {req.people_affected != null ? req.people_affected : "—"}
                  </td>
                  <td style={{ padding: "12px 14px", color: "var(--text-secondary)", fontFamily: "'DM Mono', monospace", fontSize: "11px" }}>
                    {req.created_at ? new Date(req.created_at).toLocaleDateString() : "—"}
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

