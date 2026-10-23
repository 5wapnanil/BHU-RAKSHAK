"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";
import {
  HeartHandshake,
  CheckCircle,
  Clock,
  XCircle,
  Search,
  ServerCrash,
  ArrowRight,
  Phone,
  MapPin,
} from "lucide-react";
import type { EmergencyRequest } from "@/types/coordination";

const STATUS_COLORS: Record<string, string> = {
  pending: "var(--amber)",
  in_progress: "#3b82f6",
  resolved: "var(--green)",
  cancelled: "var(--text-secondary)",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "var(--text-secondary)";
  const iconMap: Record<string, React.ReactNode> = {
    pending: <Clock size={12} />,
    in_progress: <CheckCircle size={12} />,
    resolved: <CheckCircle size={12} />,
    cancelled: <XCircle size={12} />,
  };
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
      {iconMap[status] || null}
      {status.replace(/_/g, " ")}
    </span>
  );
}

interface VolunteerRegistration {
  id: string;
  name: string;
  phone: string;
  location: string | null;
  category: string | null;
  availability: string | null;
  description: string | null;
  quantity: string | null;
  created_at: string;
  status: string;
}

function VolunteerCard({ vol }: { vol: VolunteerRegistration }) {
  return (
    <Motion variants={cardReveal}>
      <div
        className="card"
        style={{ borderTop: `3px solid var(--green)` }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "12px",
          }}
        >
          <StatusBadge status={vol.status} />
          <Link
            href={`/app-backend/requests/${vol.id}`}
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
              fontSize: "16px",
              fontWeight: 700,
              color: "var(--text-primary)",
              marginBottom: "4px",
            }}
          >
            {vol.name}
          </div>
          {vol.phone && (
            <a
              href={`tel:${vol.phone}`}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                fontFamily: "'DM Mono', monospace",
                fontSize: "12px",
                color: "var(--accent)",
                textDecoration: "none",
              }}
            >
              <Phone size={12} /> {vol.phone}
            </a>
          )}
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "8px",
            marginBottom: "12px",
          }}
        >
          {vol.category && (
            <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                CATEGORY
              </div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px", textTransform: "capitalize" }}>
                {vol.category}
              </div>
            </div>
          )}
          {vol.quantity && (
            <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                QUANTITY
              </div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                {vol.quantity}
              </div>
            </div>
          )}
        </div>

        {vol.location && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 10px",
              background: "var(--surface)",
              borderRadius: "4px",
              marginBottom: "12px",
              fontFamily: "'DM Mono', monospace",
              fontSize: "11px",
              color: "var(--text-secondary)",
            }}
          >
            <MapPin size={12} /> {vol.location}
          </div>
        )}

        {vol.availability && (
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
            Available: {vol.availability}
          </div>
        )}

        {vol.description && (
          <div
            style={{
              padding: "8px 10px",
              background: "var(--surface)",
              borderRadius: "4px",
              fontFamily: "'DM Mono', monospace",
              fontSize: "11px",
              color: "var(--text-secondary)",
              borderTop: "1px solid var(--line)",
              marginTop: "8px",
              paddingTop: "12px",
            }}
          >
            {vol.description}
          </div>
        )}

        <div
          style={{
            borderTop: "1px solid var(--line)",
            paddingTop: "12px",
            marginTop: "12px",
            fontFamily: "'DM Mono', monospace",
            fontSize: "10px",
            color: "var(--text-secondary)",
          }}
        >
          Registered: {new Date(vol.created_at).toLocaleDateString()}
        </div>
      </div>
    </Motion>
  );
}

export default function ReliefVolunteersPage() {
  const [requests, setRequests] = useState<EmergencyRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await apiFetch<EmergencyRequest[]>("/api/requests?limit=200");
        if (!cancelled) setRequests(data);
      } catch {
        if (!cancelled) setError("Failed to load relief volunteers");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const volunteers = useMemo(() => {
    return requests
      .filter((r) => r.request_type === "relief_volunteer")
      .map((r): VolunteerRegistration => {
        const p = (r.payload || {}) as Record<string, unknown>;
        return {
          id: r.id,
          name: (p.name as string) || r.contact_name || "Unknown",
          phone: (p.phone as string) || r.contact_phone || "",
          location: (p.location as string) || r.location_text || null,
          category: (p.category as string) || null,
          availability: (p.availability as string) || null,
          description: (p.description as string) || null,
          quantity: (p.quantity as string) || null,
          created_at: r.created_at || "",
          status: r.status,
        };
      });
  }, [requests]);

  const filtered = useMemo(() => {
    let result = volunteers;
    if (statusFilter !== "all") {
      result = result.filter((v) => v.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (v) =>
          v.name.toLowerCase().includes(q) ||
          v.phone.includes(q) ||
          (v.location && v.location.toLowerCase().includes(q)) ||
          (v.category && v.category.toLowerCase().includes(q))
      );
    }
    return result;
  }, [volunteers, statusFilter, searchQuery]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { all: volunteers.length, pending: 0, in_progress: 0, resolved: 0, cancelled: 0 };
    for (const v of volunteers) {
      if (counts[v.status] !== undefined) counts[v.status]++;
    }
    return counts;
  }, [volunteers]);

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Relief Volunteers</h1>
          <p>Loading relief volunteer data...</p>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px" }}>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card" style={{ borderTop: "3px solid var(--line)" }}>
              <div className="skeleton" style={{ width: "60%", height: 12, marginBottom: 12 }} />
              <div className="skeleton" style={{ width: "80%", height: 16, marginBottom: 10 }} />
              <div className="skeleton" style={{ width: "100%", height: 10, marginBottom: 6 }} />
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
          <h1>Relief Volunteers</h1>
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
          <HeartHandshake size={20} style={{ color: "var(--green)" }} />
          <h1 style={{ margin: 0 }}>Relief Volunteers</h1>
        </div>
        <p>{volunteers.length} volunteer{volunteers.length !== 1 ? "s" : ""} registered for relief operations</p>
      </div>

      <div style={{ display: "flex", gap: "12px", marginBottom: "24px", flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 12px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "4px", flex: "1 1 200px", maxWidth: "300px" }}>
          <Search size={14} style={{ color: "var(--text-secondary)", flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Search name, phone, location..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ border: "none", background: "transparent", outline: "none", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", width: "100%" }}
          />
        </div>
        <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
          {(["all", "pending", "in_progress", "resolved", "cancelled"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              style={{
                padding: "6px 12px",
                borderRadius: "4px",
                border: statusFilter === f ? "1px solid var(--accent)" : "1px solid var(--line)",
                background: statusFilter === f ? "var(--accent)" : "transparent",
                color: statusFilter === f ? "#fff" : "var(--text-secondary)",
                fontFamily: "'DM Mono', monospace",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {f === "all" ? "ALL" : f.toUpperCase().replace("_", " ")} ({statusCounts[f] ?? 0})
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div style={{ padding: "48px 24px", textAlign: "center", background: "var(--surface)", borderRadius: "8px", border: "1px solid var(--line)" }}>
          <HeartHandshake size={32} style={{ color: "var(--text-secondary)", marginBottom: "12px" }} />
          <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", marginBottom: "8px" }}>
            No relief volunteers found
          </div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-secondary)" }}>
            {searchQuery
              ? "Try adjusting your search or filter criteria"
              : statusFilter !== "all"
                ? `No relief volunteers with status "${statusFilter.replace("_", " ")}"`
                : "No relief volunteers have registered yet"}
          </div>
        </div>
      ) : (
        <Motion initial="hidden" animate="visible" variants={staggerContainer}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "16px" }}>
            {filtered.map((vol) => (
              <VolunteerCard key={vol.id} vol={vol} />
            ))}
          </div>
        </Motion>
      )}

      <div style={{ marginTop: "24px", padding: "16px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "4px", fontFamily: "'DM Mono', monospace", fontSize: "10px", letterSpacing: "1px", color: "var(--text-secondary)" }}>
        NOTE: Authentication/RBAC is not yet implemented. Volunteer actions are not secured.
      </div>
    </div>
  );
}

