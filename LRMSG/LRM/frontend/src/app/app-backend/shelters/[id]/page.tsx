"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Shelter } from "@/types/coordination";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";
import {
  ArrowLeft,
  CheckCircle,
  Clock,
  XCircle,
  ServerCrash,
  Home,
  Phone,
  Users,
  Save,
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_COLORS: Record<string, string> = {
  open: "var(--green)",
  full: "var(--amber)",
  closed: "var(--red)",
};

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || "var(--text-secondary)";
  const iconMap: Record<string, React.ReactNode> = {
    open: <CheckCircle size={12} />,
    full: <Clock size={12} />,
    closed: <XCircle size={12} />,
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
      <span style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>
        {label}
      </span>
      <span style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-secondary)", textAlign: "right", wordBreak: "break-all" }}>
        {value}
      </span>
    </div>
  );
}

function CapacityBar({ current, max }: { current: number; max: number }) {
  const pct = max > 0 ? Math.min((current / max) * 100, 100) : 0;
  const color = pct >= 90 ? "var(--red)" : pct >= 70 ? "var(--amber)" : "var(--green)";
  return (
    <div style={{ width: "100%", height: "8px", background: "var(--line)", borderRadius: "4px", overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: "4px", transition: "width 0.3s" }} />
    </div>
  );
}

export default function ShelterDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [shelter, setShelter] = useState<Shelter | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: "",
    address: "",
    capacity: "",
    contact_phone: "",
    status: "",
  });
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await apiFetch<Shelter>(`/api/shelters/${id}`);
        if (!cancelled) setShelter(data);
      } catch {
        if (!cancelled) setError("Shelter not found");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [id]);

  function startEdit() {
    if (!shelter) return;
    setEditForm({
      name: shelter.name,
      address: shelter.address || "",
      capacity: String(shelter.capacity),
      contact_phone: shelter.contact_phone || "",
      status: shelter.status,
    });
    setEditing(true);
    setSaveError(null);
    setSaveSuccess(false);
  }

  async function handleSave() {
    setSaveLoading(true);
    setSaveError(null);
    setSaveSuccess(false);

    const body: Record<string, unknown> = {};
    if (editForm.name.trim()) body.name = editForm.name.trim();
    if (editForm.address.trim()) body.address = editForm.address.trim();
    if (editForm.capacity) {
      const cap = parseInt(editForm.capacity, 10);
      if (isNaN(cap) || cap < 0) {
        setSaveError("Capacity must be 0 or greater");
        setSaveLoading(false);
        return;
      }
      body.capacity = cap;
    }
    if (editForm.contact_phone.trim()) body.contact_phone = editForm.contact_phone.trim();
    if (editForm.status) body.status = editForm.status;

    try {
      const res = await fetch(`${API}/api/shelters/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(detail?.detail || `Update failed (${res.status})`);
      }
      const updated: Shelter = await res.json();
      setShelter(updated);
      setEditing(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e: any) {
      setSaveError(e.message || "Update failed");
    } finally {
      setSaveLoading(false);
    }
  }

  if (loading) {
    return (
      <div>
        <Link href="/app-backend/shelters" style={{ display: "inline-flex", alignItems: "center", gap: "6px", font: "600 11px 'DM Mono'", color: "var(--text-secondary)", textDecoration: "none", marginBottom: "24px", letterSpacing: "0.5px" }}>
          <ArrowLeft size={14} /> BACK TO SHELTERS
        </Link>
        <div className="analytics-header"><h1>Loading shelter...</h1></div>
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

  if (error || !shelter) {
    return (
      <div>
        <Link href="/app-backend/shelters" style={{ display: "inline-flex", alignItems: "center", gap: "6px", font: "600 11px 'DM Mono'", color: "var(--text-secondary)", textDecoration: "none", marginBottom: "24px", letterSpacing: "0.5px" }}>
          <ArrowLeft size={14} /> BACK TO SHELTERS
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "24px", background: "#fee2e2", borderRadius: "8px", border: "1px solid #fca5a5", fontFamily: "'DM Mono', monospace", fontSize: "13px", color: "#991b1b" }}>
          <ServerCrash size={20} />
          {error || "Shelter not found"}
        </div>
      </div>
    );
  }

  const available = Math.max(0, shelter.capacity - shelter.current_occupancy);

  return (
    <div>
      <div className="analytics-header">
        <Link href="/app-backend/shelters" style={{ display: "inline-flex", alignItems: "center", gap: "6px", font: "600 11px 'DM Mono'", color: "var(--text-secondary)", textDecoration: "none", marginBottom: "16px", letterSpacing: "0.5px" }}>
          <ArrowLeft size={14} /> BACK TO SHELTERS
        </Link>
        <h1>Shelter Detail</h1>
        <p>View and manage this shelter</p>
      </div>

      {saveError && (
        <div style={{ padding: "12px 16px", marginBottom: "16px", background: "#fee2e2", borderRadius: "6px", border: "1px solid #fca5a5", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "#991b1b" }}>
          {saveError}
        </div>
      )}

      {saveSuccess && (
        <div style={{ padding: "12px 16px", marginBottom: "16px", background: "#dcfce7", borderRadius: "6px", border: "1px solid #86efac", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "#166534" }}>
          Shelter updated successfully.
        </div>
      )}

      <Motion initial="hidden" animate="visible" variants={staggerContainer}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
          <StatusBadge status={shelter.status} />
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "18px", fontWeight: 600, color: "var(--text-primary)" }}>
            {shelter.name}
          </span>
        </div>

        <div className="card" style={{ marginBottom: "16px" }}>
          <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ margin: 0 }}>CAPACITY</p>
          </div>
          <div style={{ marginBottom: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "'DM Mono', monospace", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "6px" }}>
              <span>{shelter.current_occupancy} / {shelter.capacity} occupied</span>
              <span>{available} available</span>
            </div>
            <CapacityBar current={shelter.current_occupancy} max={shelter.capacity} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
            <div style={{ textAlign: "center", padding: "10px", background: "var(--surface)", borderRadius: "4px" }}>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>CURRENT</div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>{shelter.current_occupancy}</div>
            </div>
            <div style={{ textAlign: "center", padding: "10px", background: "var(--surface)", borderRadius: "4px" }}>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>CAPACITY</div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>{shelter.capacity}</div>
            </div>
            <div style={{ textAlign: "center", padding: "10px", background: "var(--surface)", borderRadius: "4px" }}>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>AVAILABLE</div>
              <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "16px", fontWeight: 600, color: "var(--green)", marginTop: "2px" }}>{available}</div>
            </div>
          </div>
        </div>

        {!editing ? (
          <div className="card" style={{ marginBottom: "16px" }}>
            <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <p className="eyebrow" style={{ margin: 0 }}>SHELTER INFORMATION</p>
              <button onClick={startEdit} style={{ padding: "6px 12px", borderRadius: "4px", border: "1px solid var(--accent)", background: "transparent", color: "var(--accent)", fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, cursor: "pointer" }}>
                Edit
              </button>
            </div>
            <div style={{ display: "grid", gap: "8px" }}>
              <DetailRow label="Shelter ID" value={shelter.id} />
              <DetailRow label="Name" value={shelter.name} />
              <DetailRow label="Address" value={shelter.address || "—"} />
              <DetailRow label="Status" value={shelter.status} />
              <DetailRow label="Capacity" value={String(shelter.capacity)} />
              <DetailRow label="Current Occupancy" value={String(shelter.current_occupancy)} />
              <DetailRow label="Contact Phone" value={shelter.contact_phone || "—"} />
              <DetailRow label="Operated By" value={shelter.operated_by || "—"} />
            </div>
          </div>
        ) : (
          <div className="card" style={{ marginBottom: "16px", borderTop: "3px solid var(--accent)" }}>
            <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
              <p className="eyebrow" style={{ margin: 0 }}>EDIT SHELTER</p>
            </div>
            <div style={{ display: "grid", gap: "12px" }}>
              <div>
                <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>NAME</label>
                <input type="text" value={editForm.name} onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))} maxLength={200} style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }} />
              </div>
              <div>
                <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>ADDRESS</label>
                <input type="text" value={editForm.address} onChange={(e) => setEditForm((p) => ({ ...p, address: e.target.value }))} maxLength={500} style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>CAPACITY</label>
                  <input type="number" value={editForm.capacity} onChange={(e) => setEditForm((p) => ({ ...p, capacity: e.target.value }))} min="0" style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }} />
                </div>
                <div>
                  <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>STATUS</label>
                  <select value={editForm.status} onChange={(e) => setEditForm((p) => ({ ...p, status: e.target.value }))} style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }}>
                    <option value="open">Open</option>
                    <option value="full">Full</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              </div>
              <div>
                <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>CONTACT PHONE</label>
                <input type="text" value={editForm.contact_phone} onChange={(e) => setEditForm((p) => ({ ...p, contact_phone: e.target.value }))} maxLength={50} style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }} />
              </div>
              <div style={{ display: "flex", gap: "10px", marginTop: "4px" }}>
                <button onClick={handleSave} disabled={saveLoading} style={{ flex: "1 1 auto", padding: "10px 20px", borderRadius: "4px", border: "1px solid var(--green)", background: "var(--green)", color: "#fff", fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, cursor: saveLoading ? "not-allowed" : "pointer", opacity: saveLoading ? 0.6 : 1 }}>
                  <Save size={14} style={{ marginRight: "6px", verticalAlign: "middle" }} />
                  {saveLoading ? "Saving..." : "Save Changes"}
                </button>
                <button onClick={() => setEditing(false)} disabled={saveLoading} style={{ padding: "10px 20px", borderRadius: "4px", border: "1px solid var(--line)", background: "transparent", color: "var(--text-secondary)", fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, cursor: saveLoading ? "not-allowed" : "pointer" }}>
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="card" style={{ marginBottom: "16px" }}>
          <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
            <p className="eyebrow" style={{ margin: 0 }}>TIMESTAMPS</p>
          </div>
          <div style={{ display: "grid", gap: "8px" }}>
            <DetailRow label="Created At" value={new Date(shelter.created_at).toLocaleString()} />
            <DetailRow label="Updated At" value={new Date(shelter.updated_at).toLocaleString()} />
          </div>
        </div>

        {shelter.facilities && Object.keys(shelter.facilities).length > 0 && (
          <div className="card" style={{ marginBottom: "16px" }}>
            <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
              <p className="eyebrow" style={{ margin: 0 }}>FACILITIES</p>
            </div>
            <div style={{ display: "grid", gap: "6px" }}>
              {Object.entries(shelter.facilities).map(([key, val]) => (
                <div key={key} style={{ display: "flex", justifyContent: "space-between", padding: "8px 12px", background: "var(--surface)", borderRadius: "4px", border: "1px solid var(--line)" }}>
                  <span style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-primary)", textTransform: "capitalize" }}>{key.replace(/_/g, " ")}</span>
                  <span style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", color: "var(--text-secondary)" }}>{String(val)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {shelter.location && (
          <div className="card" style={{ marginBottom: "16px" }}>
            <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px" }}>
              <p className="eyebrow" style={{ margin: 0 }}>LOCATION</p>
            </div>
            <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-secondary)", padding: "8px 12px", background: "var(--surface)", borderRadius: "4px", border: "1px solid var(--line)", wordBreak: "break-all" }}>
              {shelter.location}
            </div>
          </div>
        )}
      </Motion>

      <div style={{ marginTop: "24px", padding: "16px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "4px", fontFamily: "'DM Mono', monospace", fontSize: "10px", letterSpacing: "1px", color: "var(--text-secondary)" }}>
        NOTE: Authentication/RBAC is not yet implemented. Shelter actions are not secured.
      </div>
    </div>
  );
}

