"use client";

import { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { ReliefResource, Assignment } from "@/types/coordination";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";
import {
  ArrowLeft,
  CheckCircle,
  Clock,
  AlertTriangle,
  XCircle,
  ServerCrash,
  Package,
  Send,
  RotateCcw,
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_COLORS: Record<string, string> = {
  available: "var(--green)",
  allocated: "#3b82f6",
  depleted: "var(--amber)",
  expired: "var(--red)",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "var(--text-secondary)";
  const iconMap: Record<string, React.ReactNode> = {
    available: <CheckCircle size={12} />,
    allocated: <Clock size={12} />,
    depleted: <AlertTriangle size={12} />,
    expired: <XCircle size={12} />,
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
          wordBreak: "break-all",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function AllocateForm({
  resourceId,
  availableQuantity,
  unit,
  onSuccess,
  onCancel,
}: {
  resourceId: string;
  availableQuantity: number | null;
  unit: string | null;
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const [requestId, setRequestId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!requestId.trim()) {
      setError("Request ID is required");
      return;
    }

    const qty = parseFloat(quantity);
    if (isNaN(qty) || qty <= 0) {
      setError("Quantity must be greater than 0");
      return;
    }
    if (availableQuantity != null && qty > availableQuantity) {
      setError(`Quantity cannot exceed available amount (${availableQuantity})`);
      return;
    }

    setLoading(true);
    try {
      const body: Record<string, unknown> = {
        request_id: requestId.trim(),
        quantity: qty,
      };
      if (notes.trim()) {
        body.notes = notes.trim();
      }
      await fetch(`${API}/api/relief-resources/${resourceId}/allocate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).then(async (res) => {
        if (!res.ok) {
          const detail = await res.json().catch(() => null);
          throw new Error(detail?.detail || `Allocation failed (${res.status})`);
        }
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Allocation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ marginTop: "16px", borderTop: "3px solid #3b82f6" }}>
      <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
        <p className="eyebrow" style={{ margin: 0 }}>ALLOCATE RESOURCE</p>
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
              REQUEST ID (UUID) *
            </label>
            <input
              type="text"
              placeholder="Paste the emergency request UUID"
              value={requestId}
              onChange={(e) => setRequestId(e.target.value)}
              required
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

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                QUANTITY *
              </label>
              <input
                type="number"
                placeholder={`Max: ${availableQuantity ?? "—"}`}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                min="0.01"
                max="1000000"
                step="any"
                required
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
              <div
                style={{
                  padding: "8px 12px",
                  border: "1px solid var(--line)",
                  borderRadius: "4px",
                  background: "var(--surface)",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "12px",
                  color: "var(--text-secondary)",
                }}
              >
                {unit || "—"}
              </div>
            </div>
          </div>

          <div>
            <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
              NOTES
            </label>
            <input
              type="text"
              placeholder="Optional allocation notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              maxLength={2000}
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

          <div style={{ display: "flex", gap: "10px", marginTop: "4px" }}>
            <button
              type="submit"
              disabled={loading}
              style={{
                flex: "1 1 auto",
                padding: "10px 20px",
                borderRadius: "4px",
                border: "1px solid #3b82f6",
                background: "#3b82f6",
                color: "#fff",
                fontFamily: "'DM Mono', monospace",
                fontSize: "12px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? "Allocating..." : "Allocate"}
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

export default function ResourceDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [resource, setResource] = useState<ReliefResource | null>(null);
  const [allocations, setAllocations] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllocate, setShowAllocate] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [releaseLoading, setReleaseLoading] = useState<string | null>(null);

  async function loadData() {
    try {
      const [res, assigns] = await Promise.allSettled([
        apiFetch<ReliefResource>(`/api/relief-resources/${id}`),
        apiFetch<Assignment[]>("/api/assignments?limit=100"),
      ]);
      if (res.status === "fulfilled") setResource(res.value);
      else setError("Resource not found");
      if (assigns.status === "fulfilled") {
        setAllocations(
          assigns.value.filter(
            (a) =>
              a.resource_id === id &&
              a.assignment_type === "resource" &&
              a.status !== "cancelled"
          )
        );
      }
    } catch {
      setError("Failed to load resource");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [id]);

  async function handleRelease(assignmentId: string) {
    setReleaseLoading(assignmentId);
    setActionError(null);
    try {
      const res = await fetch(
        `${API}/api/relief-resources/allocations/${assignmentId}/release`,
        { method: "POST" }
      );
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(detail?.detail || `Release failed (${res.status})`);
      }
      await loadData();
    } catch (e: any) {
      setActionError(e.message || "Release failed");
      setTimeout(() => setActionError(null), 5000);
    } finally {
      setReleaseLoading(null);
    }
  }

  if (loading) {
    return (
      <div>
        <Link
          href="/app-backend/resources"
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
          <ArrowLeft size={14} /> BACK TO RESOURCES
        </Link>
        <div className="analytics-header">
          <h1>Loading resource...</h1>
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

  if (error || !resource) {
    return (
      <div>
        <Link
          href="/app-backend/resources"
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
          <ArrowLeft size={14} /> BACK TO RESOURCES
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
          {error || "Resource not found"}
        </div>
      </div>
    );
  }

  const canAllocate =
    (resource.status === "available" || resource.status === "allocated") &&
    resource.available_quantity != null &&
    resource.available_quantity > 0;

  return (
    <div>
      <div className="analytics-header">
        <Link
          href="/app-backend/resources"
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
          <ArrowLeft size={14} /> BACK TO RESOURCES
        </Link>
        <h1>Resource Detail</h1>
        <p>View and manage this relief resource</p>
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
          <StatusBadge status={resource.status} />
          <span
            style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "18px",
              fontWeight: 600,
              color: "var(--text-primary)",
            }}
          >
            {resource.resource_type}
          </span>
        </div>

        <div className="card" style={{ marginBottom: "16px" }}>
          <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ margin: 0 }}>RESOURCE INFORMATION</p>
          </div>
          <div style={{ display: "grid", gap: "8px" }}>
            <DetailRow label="Resource ID" value={resource.id} />
            <DetailRow label="Type" value={resource.resource_type} />
            <DetailRow label="Description" value={resource.description || "—"} />
            <DetailRow
              label="Total Quantity"
              value={
                resource.quantity != null
                  ? `${resource.quantity} ${resource.unit || ""}`.trim()
                  : "—"
              }
            />
            <DetailRow
              label="Available Quantity"
              value={
                resource.available_quantity != null
                  ? `${resource.available_quantity} ${resource.unit || ""}`.trim()
                  : "—"
              }
            />
            <DetailRow label="Unit" value={resource.unit || "—"} />
            <DetailRow
              label="Provider ID"
              value={resource.provider_id || "—"}
            />
          </div>
        </div>

        <div className="card" style={{ marginBottom: "16px" }}>
          <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ margin: 0 }}>TIMESTAMPS</p>
          </div>
          <div style={{ display: "grid", gap: "8px" }}>
            <DetailRow
              label="Created At"
              value={new Date(resource.created_at).toLocaleString()}
            />
            <DetailRow
              label="Updated At"
              value={new Date(resource.updated_at).toLocaleString()}
            />
          </div>
        </div>

        {allocations.length > 0 && (
          <div className="card" style={{ marginBottom: "16px" }}>
            <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
              <p className="eyebrow" style={{ margin: 0 }}>ACTIVE ALLOCATIONS</p>
            </div>
            <div style={{ display: "grid", gap: "8px" }}>
              {allocations.map((alloc) => (
                <div
                  key={alloc.id}
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
                  <div>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", color: "var(--text-secondary)" }}>
                      Assignment: {alloc.id.slice(0, 12)}...
                    </div>
                    <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)", marginTop: "2px" }}>
                      Request: {alloc.request_id ? alloc.request_id.slice(0, 12) + "..." : "—"} • Status: {alloc.status}
                    </div>
                  </div>
                  <button
                    onClick={() => handleRelease(alloc.id)}
                    disabled={releaseLoading === alloc.id}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      padding: "6px 12px",
                      borderRadius: "4px",
                      border: "1px solid var(--line)",
                      background: "transparent",
                      color: "var(--text-secondary)",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "11px",
                      fontWeight: 600,
                      cursor: releaseLoading === alloc.id ? "not-allowed" : "pointer",
                      opacity: releaseLoading === alloc.id ? 0.6 : 1,
                    }}
                  >
                    <RotateCcw size={12} />
                    {releaseLoading === alloc.id ? "Releasing..." : "Release"}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {canAllocate && (
          <>
            {!showAllocate && (
              <button
                onClick={() => setShowAllocate(true)}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "10px 20px",
                  borderRadius: "4px",
                  border: "1px solid #3b82f6",
                  background: "#3b82f6",
                  color: "#fff",
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: "pointer",
                  marginBottom: "16px",
                }}
              >
                <Send size={14} />
                Allocate to Request
              </button>
            )}
            {showAllocate && (
              <AllocateForm
                resourceId={id}
                availableQuantity={resource.available_quantity}
                unit={resource.unit}
                onSuccess={() => {
                  setShowAllocate(false);
                  loadData();
                }}
                onCancel={() => setShowAllocate(false)}
              />
            )}
          </>
        )}

        {!canAllocate && (
          <div className="card" style={{ marginBottom: "16px" }}>
            <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
              <p className="eyebrow" style={{ margin: 0 }}>ALLOCATIONS</p>
            </div>
            <div
              style={{
                fontFamily: "'DM Mono', monospace",
                fontSize: "12px",
                color: "var(--text-secondary)",
              }}
            >
              This resource cannot be allocated.
              {resource.status === "depleted" && " It is fully depleted."}
              {resource.status === "expired" && " It has expired."}
              {resource.available_quantity != null && resource.available_quantity <= 0 && " Available quantity is zero."}
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
        NOTE: Authentication/RBAC is not yet implemented. Resource actions are not secured.
      </div>
    </div>
  );
}

