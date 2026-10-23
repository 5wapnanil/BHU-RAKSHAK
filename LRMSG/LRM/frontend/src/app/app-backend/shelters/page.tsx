"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { Shelter } from "@/types/coordination";
import { Motion } from "@/components/ui/Motion";
import { staggerContainer, cardReveal } from "@/animations/variants";
import {
  Home,
  CheckCircle,
  Clock,
  XCircle,
  ArrowRight,
  ServerCrash,
  Search,
  Plus,
  X,
  Users,
  Phone,
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STATUS_OPTIONS = [
  { value: "all", label: "All" },
  { value: "open", label: "Open" },
  { value: "full", label: "Full" },
  { value: "closed", label: "Closed" },
];

const STATUS_COLORS: Record<string, string> = {
  open: "var(--green)",
  full: "var(--amber)",
  closed: "var(--red)",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  open: <CheckCircle size={12} />,
  full: <Clock size={12} />,
  closed: <XCircle size={12} />,
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

function CapacityBar({ current, max }: { current: number; max: number }) {
  const pct = max > 0 ? Math.min((current / max) * 100, 100) : 0;
  const color = pct >= 90 ? "var(--red)" : pct >= 70 ? "var(--amber)" : "var(--green)";
  return (
    <div style={{ width: "100%", height: "6px", background: "var(--line)", borderRadius: "3px", overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: "3px", transition: "width 0.3s" }} />
    </div>
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

function CreateShelterForm({
  onSuccess,
  onCancel,
}: {
  onSuccess: () => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    name: "",
    address: "",
    capacity: "",
    contact_phone: "",
    operated_by: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateField(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!form.name.trim()) {
      setError("Shelter name is required");
      return;
    }

    const body: Record<string, unknown> = {
      name: form.name.trim(),
    };

    if (form.address.trim()) body.address = form.address.trim();
    if (form.capacity) {
      const cap = parseInt(form.capacity, 10);
      if (isNaN(cap) || cap < 0) {
        setError("Capacity must be 0 or greater");
        return;
      }
      body.capacity = cap;
    }
    if (form.contact_phone.trim()) body.contact_phone = form.contact_phone.trim();
    if (form.operated_by.trim()) body.operated_by = form.operated_by.trim();

    setLoading(true);
    try {
      await apiFetch<Shelter>("/api/shelters", {
        method: "POST",
        body: JSON.stringify(body),
      });
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to create shelter");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: "24px", borderTop: "3px solid var(--green)" }}>
      <div style={{ borderBottom: "1px solid var(--line)", paddingBottom: "12px", marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <p className="eyebrow" style={{ margin: 0 }}>CREATE SHELTER</p>
        <button onClick={onCancel} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", padding: "4px" }}>
          <X size={16} />
        </button>
      </div>

      {error && (
        <div style={{ padding: "10px 14px", marginBottom: "16px", background: "#fee2e2", borderRadius: "6px", border: "1px solid #fca5a5", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "#991b1b" }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ display: "grid", gap: "12px" }}>
          <div>
            <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
              SHELTER NAME *
            </label>
            <input
              type="text"
              placeholder="e.g. Community Center, School Gym"
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              required
              maxLength={200}
              style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }}
            />
          </div>

          <div>
            <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
              ADDRESS
            </label>
            <input
              type="text"
              placeholder="Street address..."
              value={form.address}
              onChange={(e) => updateField("address", e.target.value)}
              maxLength={500}
              style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                CAPACITY
              </label>
              <input
                type="number"
                placeholder="0"
                value={form.capacity}
                onChange={(e) => updateField("capacity", e.target.value)}
                min="0"
                max="100000"
                style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }}
              />
            </div>
            <div>
              <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
                CONTACT PHONE
              </label>
              <input
                type="text"
                placeholder="Phone number"
                value={form.contact_phone}
                onChange={(e) => updateField("contact_phone", e.target.value)}
                maxLength={50}
                style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }}
              />
            </div>
          </div>

          <div>
            <label style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: "4px" }}>
              OPERATED BY (USER ID)
            </label>
            <input
              type="text"
              placeholder="Optional user UUID"
              value={form.operated_by}
              onChange={(e) => updateField("operated_by", e.target.value)}
              style={{ width: "100%", padding: "8px 12px", border: "1px solid var(--line)", borderRadius: "4px", background: "var(--surface)", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", outline: "none", boxSizing: "border-box" }}
            />
          </div>

          <div style={{ display: "flex", gap: "10px", marginTop: "8px" }}>
            <button
              type="submit"
              disabled={loading}
              style={{ flex: "1 1 auto", padding: "10px 20px", borderRadius: "4px", border: "1px solid var(--green)", background: "var(--green)", color: "#fff", fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.6 : 1 }}
            >
              {loading ? "Creating..." : "Create Shelter"}
            </button>
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              style={{ padding: "10px 20px", borderRadius: "4px", border: "1px solid var(--line)", background: "transparent", color: "var(--text-secondary)", fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, cursor: loading ? "not-allowed" : "pointer" }}
            >
              Cancel
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default function SheltersPage() {
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [showCreate, setShowCreate] = useState(false);

  async function loadShelters() {
    try {
      const data = await apiFetch<Shelter[]>("/api/shelters?limit=100");
      setShelters(data);
      setError(null);
    } catch {
      setError("Failed to load shelters");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadShelters();
  }, []);

  const filtered = useMemo(() => {
    let result = shelters;
    if (statusFilter !== "all") {
      result = result.filter((s) => s.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (s) =>
          s.id.toLowerCase().includes(q) ||
          s.name.toLowerCase().includes(q) ||
          (s.address && s.address.toLowerCase().includes(q))
      );
    }
    return result;
  }, [shelters, statusFilter, searchQuery]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { all: shelters.length };
    for (const opt of STATUS_OPTIONS) {
      if (opt.value !== "all") counts[opt.value] = 0;
    }
    for (const s of shelters) {
      if (counts[s.status] !== undefined) counts[s.status]++;
    }
    return counts;
  }, [shelters]);

  if (loading) {
    return (
      <div>
        <div className="analytics-header">
          <h1>Shelters</h1>
          <p>Loading shelter data...</p>
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
          <h1>Shelters</h1>
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
        <h1>Shelters</h1>
        <p>{shelters.length} total shelters</p>
      </div>

      <div style={{ marginBottom: "24px" }}>
        <button
          onClick={() => setShowCreate(!showCreate)}
          style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "8px 16px", borderRadius: "4px", border: "1px solid var(--green)", background: showCreate ? "transparent" : "var(--green)", color: showCreate ? "var(--text-secondary)" : "#fff", fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, cursor: "pointer" }}
        >
          <Plus size={14} />
          {showCreate ? "Cancel" : "Create Shelter"}
        </button>
      </div>

      {showCreate && (
        <CreateShelterForm
          onSuccess={() => { setShowCreate(false); loadShelters(); }}
          onCancel={() => setShowCreate(false)}
        />
      )}

      <div style={{ display: "flex", gap: "12px", marginBottom: "24px", flexWrap: "wrap", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 12px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "4px", flex: "1 1 200px", maxWidth: "300px" }}>
          <Search size={14} style={{ color: "var(--text-secondary)", flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Search name, address, ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ border: "none", background: "transparent", outline: "none", fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", width: "100%" }}
          />
        </div>

        <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              style={{ padding: "6px 12px", borderRadius: "4px", border: statusFilter === opt.value ? "1px solid var(--accent)" : "1px solid var(--line)", background: statusFilter === opt.value ? "var(--accent)" : "transparent", color: statusFilter === opt.value ? "#fff" : "var(--text-secondary)", fontFamily: "'DM Mono', monospace", fontSize: "11px", fontWeight: 600, cursor: "pointer" }}
            >
              {opt.label} ({statusCounts[opt.value] ?? 0})
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div style={{ padding: "48px 24px", textAlign: "center", background: "var(--surface)", borderRadius: "8px", border: "1px solid var(--line)" }}>
          <Home size={32} style={{ color: "var(--text-secondary)", marginBottom: "12px" }} />
          <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", marginBottom: "8px" }}>
            No shelters found
          </div>
          <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-secondary)" }}>
            {searchQuery ? "Try adjusting your search or filter criteria" : statusFilter !== "all" ? `No shelters with status "${statusFilter}"` : "No shelters have been registered yet"}
          </div>
        </div>
      ) : (
        <Motion initial="hidden" animate="visible" variants={staggerContainer}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "16px" }}>
            {filtered.map((shelter) => {
              const available = Math.max(0, shelter.capacity - shelter.current_occupancy);
              return (
                <Motion key={shelter.id} variants={cardReveal}>
                  <div className="card" style={{ borderTop: `3px solid ${STATUS_COLORS[shelter.status] || "var(--line)"}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                      <StatusBadge status={shelter.status} />
                      <Link href={`/app-backend/shelters/${shelter.id}`} style={{ display: "flex", alignItems: "center", gap: "4px", fontFamily: "'DM Mono', monospace", fontSize: "11px", color: "var(--accent)", textDecoration: "none" }}>
                        Details <ArrowRight size={12} />
                      </Link>
                    </div>

                    <div style={{ marginBottom: "12px" }}>
                      <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "15px", fontWeight: 600, color: "var(--text-primary)", marginBottom: "2px" }}>
                        {shelter.name}
                      </div>
                      {shelter.address && (
                        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "11px", color: "var(--text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {shelter.address}
                        </div>
                      )}
                    </div>

                    <div style={{ marginBottom: "12px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)", marginBottom: "4px" }}>
                        <span>{shelter.current_occupancy} / {shelter.capacity}</span>
                        <span>{available} available</span>
                      </div>
                      <CapacityBar current={shelter.current_occupancy} max={shelter.capacity} />
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "12px" }}>
                      <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
                        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                          OCCUPANCY
                        </div>
                        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                          {shelter.current_occupancy}
                        </div>
                      </div>
                      <div style={{ textAlign: "center", padding: "8px", background: "var(--surface)", borderRadius: "4px" }}>
                        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                          CAPACITY
                        </div>
                        <div style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", marginTop: "2px" }}>
                          {shelter.capacity}
                        </div>
                      </div>
                    </div>

                    {shelter.contact_phone && (
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", padding: "6px 10px", background: "var(--surface)", borderRadius: "4px", fontFamily: "'DM Mono', monospace", fontSize: "11px", color: "var(--text-secondary)", marginBottom: "8px" }}>
                        <Phone size={12} />
                        {shelter.contact_phone}
                      </div>
                    )}

                    {shelter.operated_by && (
                      <div style={{ display: "flex", alignItems: "center", gap: "6px", padding: "6px 10px", background: "var(--surface)", borderRadius: "4px", fontFamily: "'DM Mono', monospace", fontSize: "10px", color: "var(--text-secondary)" }}>
                        <Users size={12} />
                        Operator: {shelter.operated_by.slice(0, 8)}...
                      </div>
                    )}
                  </div>
                </Motion>
              );
            })}
          </div>
        </Motion>
      )}

      <div style={{ marginTop: "24px", padding: "16px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: "4px", fontFamily: "'DM Mono', monospace", fontSize: "10px", letterSpacing: "1px", color: "var(--text-secondary)" }}>
        NOTE: Authentication/RBAC is not yet implemented. Shelter actions are not secured.
      </div>
    </div>
  );
}

