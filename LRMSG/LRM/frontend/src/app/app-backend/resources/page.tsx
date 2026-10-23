"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { ReliefResource } from "@/types/coordination";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";
import {
  Package,
  CheckCircle,
  Clock,
  AlertTriangle,
  XCircle,
  ArrowRight,
  ServerCrash,
  Search,
  Plus,
  X,
} from "lucide-react";

const STATUS_OPTIONS = [
  { value: "all", label: "All" },
  { value: "available", label: "Available" },
  { value: "allocated", label: "Allocated" },
  { value: "depleted", label: "Depleted" },
  { value: "expired", label: "Expired" },
];

const STATUS_COLORS: Record<string, string> = {
  available: "var(--green)",
  allocated: "#3b82f6",
  depleted: "var(--amber)",
  expired: "var(--red)",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  available: <CheckCircle size={12} />,
  allocated: <Clock size={12} />,
  depleted: <AlertTriangle size={12} />,
  expired: <XCircle size={12} />,
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

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
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
        }}
      >
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

function CreateResourceForm({
  onSuccess,
  onCancel,
}: {
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    resource_type: "",
    description: "",
    quantity: "",
    unit: "",
    latitude: "",
    longitude: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!form.resource_type.trim()) {
      setError("Resource type is required");
      return;
    }
    if (form.resource_type.length > 100) {
      setError("Resource type must be 100 characters or less");
      return;
    }

    const body: Record<string, unknown> = {
      resource_type: form.resource_type.trim(),
    };

    if (form.description.trim()) {
      if (form.description.length > 2000) {
        setError("Description must be 2000 characters or less");
        return;
      }
      body.description = form.description.trim();
    }
    if (form.quantity) {
      const qty = parseFloat(form.quantity);
      if (isNaN(qty) || qty <= 0 || qty > 1000000) {
        setError("Quantity must be between 0 and 1,000,000");
        return;
      }
      body.quantity = qty;
    }
    if (form.unit.trim()) {
      body.unit = form.unit.trim();
    }
    if (form.latitude && form.longitude) {
      const lat = parseFloat(form.latitude);
      const lng = parseFloat(form.longitude);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        setError("Latitude must be between -90 and 90");
        return;
      }
      if (isNaN(lng) || lng < -180 || lng > 180) {
        setError("Longitude must be between -180 and 180");
        return;
      }
      body.latitude = lat;
      body.longitude = lng;
    }

    setLoading(true);
    try {
      await apiFetch<ReliefResource>("/api/relief-resources", {
        method: "POST",
        body: JSON.stringify(body),
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to create resource");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: "24px", borderTop: "3px solid var(--green)" }}>
      <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <p className="eyebrow" style={{ margin: 0 }}>CREATE RESOURCE</p>
        <button
          onClick={onCancel}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            color: "var(--text-secondary)",
            padding: "4px",
          }}
        >
          <X size={16} />
        </button>
      </div>

      {error && (
        <div
          style={{
            padding: "10px 14px",
            marginBottom: "16px",
            background: "#fee2e2",
            borderRadius: "6px",
            border: "1px solid #fca5a5",
            fontFamily: "'DM Mono', monospace",
            fontSize: "12px",
            color: "#991b1b",
          }}
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: "grid", gap: "12px" }}>
          <div>
            <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
              RESOURCE TYPE *
            </label>
            <input
              type="text"
              placeholder="e.g. Water Bottles, First Aid Kit, Blankets"
              value={form.resource_type}
              onChange={(e) => updateField("resource_type", e.target.value)}
              required
              maxLength={100}
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid var(--line)",
                borderRadius: "4px",
                background: "var(--surface)",
                fontFamily: "'DM Mono', monospace",
                fontSize: "12px",
                color: "var(--text-primary)",
                outline: "none",
                boxSizing: "border-box",
              }}
            />
          </div>

          <div>
            <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
              DESCRIPTION
            </label>
            <textarea
              placeholder="Optional description..."
              value={form.description}
              onChange={(e) => updateField("description", e.target.value)}
              maxLength={2000}
              rows={3}
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid var(--line)",
                borderRadius: "4px",
                background: "var(--surface)",
                fontFamily: "'DM Mono', monospace",
                fontSize: "12px",
                color: "var(--text-primary)",
                outline: "none",
                resize: "vertical",
                boxSizing: "border-box",
              }}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                QUANTITY
              </label>
              <input
                type="number"
                placeholder="0"
                value={form.quantity}
                onChange={(e) => updateField("quantity", e.target.value)}
                min="0.01"
                max="1000000"
                step="any"
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid var(--line)",
                  borderRadius: "4px",
                  background: "var(--surface)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "12px",
                  color: "var(--text-primary)",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
            <div>
              <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                UNIT
              </label>
              <input
                type="text"
                placeholder="e.g. kg, boxes, pieces"
                value={form.unit}
                onChange={(e) => updateField("unit", e.target.value)}
                maxLength={50}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid var(--line)",
                  borderRadius: "4px",
                  background: "var(--surface)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "12px",
                  color: "var(--text-primary)",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                LATITUDE
              </label>
              <input
                type="number"
                placeholder="-90 to 90"
                value={form.latitude}
                onChange={(e) => updateField("latitude", e.target.value)}
                min="-90"
                max="90"
                step="any"
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid var(--line)",
                  borderRadius: "4px",
                  background: "var(--surface)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "12px",
                  color: "var(--text-primary)",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
            <div>
              <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                LONGITUDE
              </label>
              <input
                type="number"
                placeholder="-180 to 180"
                value={form.longitude}
                onChange={(e) => updateField("longitude", e.target.value)}
                min="-180"
                max="180"
                step="any"
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  border: "1px solid var(--line)",
                  borderRadius: "4px",
                  background: "var(--surface)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "12px",
                  color: "var(--text-primary)",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>
          </div>

          <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
            <button
              type="submit"
              disabled={loading}
              style={{
                flex: "1 1 auto",
                padding: "10px 20px",
                borderRadius: "4px",
                border: "1px solid var(--green)",
                background: "var(--green)",
                color: "#fff",
                fontFamily: "'DM Mono', monospace",
                fontSize: "12px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? "Creating..." : "Create Resource"}
            </button>
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              style={{
                padding: "10px 20px",
                borderRadius: "4px",
                border: "1px solid var(--line)",
                background: "transparent",
                color: "var(--text-secondary)",
                fontFamily: "'DM Mono', monospace",
                fontSize: "12px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default function ResourcesPage() {
  const [resources, setResources] = useState<ReliefResource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  async function loadResources() {
    try {
      const data = await apiFetch<ReliefResource[]>("/api/relief-resources?limit=100");
      setResources(data);
      setError(null);
    } catch {
      setError("Failed to load relief resources");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadResources();
  }, []);

  const filtered = useMemo(() => {
    let result = resources;

    if (statusFilter !== "all") {
      result = result.filter((r) => r.status === statusFilter);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (r) =>
          r.id.toLowerCase().includes(q) ||
          r.resource_type.toLowerCase().includes(q) ||
          (r.description && r.description.toLowerCase().includes(q))
      );
    }

    return result;
  }, [resources, statusFilter, searchQuery]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { all: resources.length };
    for (const opt of STATUS_OPTIONS) {
      if (opt.value !== "all") counts[opt.value] = 0;
    }
    for (const r of resources) {
      if (counts[r.status] !== undefined) counts[r.status]++;
    }
    return counts;
  }, [resources]);

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Relief Resources</h1>
          <p>Loading resource data...</p>
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
          <h1>Relief Resources</h1>
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
        <h1>Relief Resources</h1>
        <p>{resources.length} total resources</p>
      </div>

      <div style={{ marginBottom: "24px" }}>
        <button
          onClick={() => setShowCreate(!showCreate)}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "8px 16px",
            borderRadius: "4px",
            border: "1px solid var(--green)",
            background: showCreate ? "transparent" : "var(--green)",
            color: showCreate ? "var(--text-secondary)" : "#fff",
            fontFamily: "'DM Mono', monospace",
            fontSize: "12px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          <Plus size={14} />
          {showCreate ? "Cancel" : "Create Resource"}
        </button>
      </div>

      {showCreate && (
        <CreateResourceForm
          onSuccess={() => {
            setShowCreate(false);
            loadResources();
          }}
          onCancel={() => setShowCreate(false)}
        />
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
            placeholder="Search type, description, ID..."
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
          <Package size={32} style={{ color: "var(--text-secondary)", marginBottom: "12px" }} />
          <div
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "16px",
              fontWeight: 600,
              color: "var(--text-primary)",
              marginBottom: "8px",
            }}
          >
            No resources found
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
                ? `No resources with status "${statusFilter}"`
                : "No relief resources have been registered yet"}
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
            {filtered.map((resource) => (
              <Motion key={resource.id} variants={cardReveal}>
                <div
                  className="card"
                  style={{ borderTop: `3px solid ${STATUS_COLORS[resource.status] || "var(--line)"}` }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      marginBottom: "12px",
                    }}
                  >
                    <StatusBadge status={resource.status} />
                    <Link
                      href={`/app-backend/resources/${resource.id}`}
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
                        fontSize: "15px",
                        fontWeight: 600,
                        color: "var(--text-primary)",
                        marginBottom: "2px",
                      }}
                    >
                      {resource.resource_type}
                    </div>
                    {resource.description && (
                      <div
                        style={{
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "11px",
                          color: "var(--text-secondary)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {resource.description}
                      </div>
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
                    <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                        QUANTITY
                      </div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                        {resource.quantity != null ? `${resource.quantity} ${resource.unit || ""}`.trim() : "—"}
                      </div>
                    </div>
                    <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                        AVAILABLE
                      </div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                        {resource.available_quantity != null ? `${resource.available_quantity} ${resource.unit || ""}`.trim() : "—"}
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
                        PROVIDER
                      </div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px", wordBreak: "break-all" }}>
                        {resource.provider_id ? resource.provider_id.slice(0, 8) + "..." : "—"}
                      </div>
                    </div>
                    <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                        CREATED
                      </div>
                      <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                        {new Date(resource.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
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
        NOTE: Authentication/RBAC is not yet implemented. Resource actions are not secured.
      </div>
    </div>
  );
}

