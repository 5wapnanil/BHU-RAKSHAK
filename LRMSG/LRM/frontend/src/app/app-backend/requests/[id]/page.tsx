"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { use } from "react";
import { apiFetch } from "@/lib/api";
import { EmergencyRequest } from "@/types/coordination";
import {
  ArrowLeft,
  MapPin,
  Clock,
  Users,
  Siren,
  ServerCrash,
  Server,
  FileText,
  Phone,
  User,
} from "lucide-react";

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
        padding: "4px 10px",
        borderRadius: "3px",
        font: "700 11px 'DM Mono'",
        letterSpacing: "0.5px",
        background: style.bg,
        color: style.color,
      }}
    >
      {label}
    </span>
  );
}

export default function RequestDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [request, setRequest] = useState<EmergencyRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<EmergencyRequest>(`/api/requests/${id}`)
      .then(setRequest)
      .catch(() => setError("Failed to load request details"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div>
        <Link href="/app-backend/requests" style={{ display: "inline-flex", alignItems: "center", gap: "6px", font: "600 11px 'DM Mono'", color: "var(--text-secondary)", textDecoration: "none", marginBottom: "24px", letterSpacing: "0.5px" }}>
          <ArrowLeft size={14} /> BACK TO REQUESTS
        </Link>
        <div className="analytics-header">
          <h1>Loading request...</h1>
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

  if (error || !request) {
    return (
      <div>
        <Link href="/app-backend/requests" style={{ display: "inline-flex", alignItems: "center", gap: "6px", font: "600 11px 'DM Mono'", color: "var(--text-secondary)", textDecoration: "none", marginBottom: "24px", letterSpacing: "0.5px" }}>
          <ArrowLeft size={14} /> BACK TO REQUESTS
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "24px", background: "#fee2e2", borderRadius: "8px", border: "1px solid #fca5a5", fontFamily: "'DM Mono', monospace", fontSize: "13px", color: "#991b1b" }}>
          <ServerCrash size={20} />
          {error || "Request not found"}
        </div>
      </div>
    );
  }

  const statusStyle = STATUS_STYLES[request.status] || { bg: "#f3f4f6", color: "#374151" };
  const serverStyle = request.server_status
    ? SERVER_STATUS_STYLES[request.server_status] || { bg: "#f3f4f6", color: "#374151" }
    : null;
  const severityStyle = request.severity
    ? SEVERITY_STYLES[request.severity] || { bg: "#f3f4f6", color: "#374151" }
    : null;

  const isRelief = request.request_type === "relief" || request.request_type === "help";
  const isEvacuation = request.request_type === "evacuation";
  const backHref = isRelief ? "/app-backend/requests/relief" : isEvacuation ? "/app-backend/requests/evacuation" : "/app-backend/requests";
  const typeLabel = isRelief ? "Relief Request" : isEvacuation ? "Evacuation Request" : "Emergency Request";

  return (
    <div>
      <Link
        href={backHref}
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
        <ArrowLeft size={14} /> BACK TO {isRelief ? "RELIEF" : isEvacuation ? "EVACUATION" : "REQUESTS"}
      </Link>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "32px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div className="eyebrow" style={{ color: "var(--accent-text)", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px" }}>
            <Siren size={14} />
            {typeLabel.toUpperCase()}
          </div>
          <h1 style={{ font: "700 28px 'Space Grotesk'", color: "var(--text-primary)", margin: "8px 0 12px", letterSpacing: "-1px", textTransform: "capitalize" }}>
            {request.request_type.replace(/_/g, " ")}
          </h1>
          <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
            <Badge label={request.status.replace(/_/g, " ")} style={statusStyle} />
            {serverStyle && <Badge label={`server: ${request.server_status}`} style={serverStyle} />}
            {severityStyle && <Badge label={request.severity!} style={severityStyle} />}
          </div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ font: "500 10px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "1px" }}>REQUEST ID</div>
          <div style={{ font: "500 11px 'DM Mono'", color: "var(--text-primary)", marginTop: "4px", wordBreak: "break-all" }}>
            {request.id}
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "24px", marginBottom: "24px" }}>
        <div className="card">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "12px" }}>
            <FileText size={16} style={{ color: "var(--accent)" }} />
            <span className="eyebrow" style={{ margin: 0 }}>DETAILS</span>
          </div>
          <div style={{ display: "grid", gap: "12px" }}>
            {[
              { label: "Request Type", value: request.request_type.replace(/_/g, " ") },
              { label: "Status", value: request.status.replace(/_/g, " ") },
              { label: "Server Status", value: request.server_status || "—" },
              { label: "Severity", value: request.severity || "—" },
              { label: "People Affected", value: request.people_affected != null ? String(request.people_affected) : "—" },
            ].map((item) => (
              <div key={item.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ font: "500 11px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "0.5px", textTransform: "uppercase" }}>{item.label}</span>
                <span style={{ font: "600 13px 'DM Sans'", color: "var(--text-primary)", textTransform: "capitalize" }}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "12px" }}>
            <User size={16} style={{ color: "var(--accent)" }} />
            <span className="eyebrow" style={{ margin: 0 }}>REQUESTER INFORMATION</span>
          </div>
          <div style={{ display: "grid", gap: "12px" }}>
            {[
              { label: "Name", value: request.contact_name || "—" },
              { label: "Phone", value: request.contact_phone || "—" },
            ].map((item) => (
              <div key={item.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ font: "500 11px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "0.5px", textTransform: "uppercase" }}>{item.label}</span>
                <span style={{ font: "600 13px 'DM Sans'", color: "var(--text-primary)" }}>{item.value}</span>
              </div>
            ))}
          </div>
          {request.contact_phone && (
            <a
              href={`tel:${request.contact_phone}`}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                marginTop: "16px",
                padding: "10px 16px",
                borderRadius: "4px",
                background: "#3FB950",
                color: "#fff",
                font: "600 12px 'DM Mono'",
                letterSpacing: "0.5px",
                textDecoration: "none",
                transition: "background 0.15s",
              }}
            >
              <Phone size={14} /> CALL REQUESTER
            </a>
          )}
        </div>

        <div className="card">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "12px" }}>
            <Clock size={16} style={{ color: "var(--accent)" }} />
            <span className="eyebrow" style={{ margin: 0 }}>TIMESTAMPS</span>
          </div>
          <div style={{ display: "grid", gap: "12px" }}>
            {[
              { label: "Created At", value: request.created_at ? new Date(request.created_at).toLocaleString() : "—" },
              { label: "Updated At", value: request.updated_at ? new Date(request.updated_at).toLocaleString() : "—" },
              { label: "Client Op ID", value: request.client_op_id || "—" },
            ].map((item) => (
              <div key={item.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ font: "500 11px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "0.5px", textTransform: "uppercase" }}>{item.label}</span>
                <span style={{ font: "500 12px 'DM Mono'", color: "var(--text-primary)", wordBreak: "break-all", textAlign: "right", maxWidth: "60%" }}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "12px" }}>
          <MapPin size={16} style={{ color: "var(--accent)" }} />
          <span className="eyebrow" style={{ margin: 0 }}>LOCATION</span>
        </div>
        <p style={{ font: "400 14px 'DM Sans'", color: request.location_text ? "var(--text-primary)" : "var(--text-secondary)", margin: 0 }}>
          {request.location_text || "No location information available."}
        </p>
      </div>

      <div style={{ padding: "16px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "4px", fontFamily: "'DM Mono', monospace", fontSize: "10px", letterSpacing: "1px", color: "var(--text-secondary)" }}>
        READ-ONLY VIEW — Mutation controls (status update, assignment) will be added in a future step.
      </div>
    </div>
  );
}

