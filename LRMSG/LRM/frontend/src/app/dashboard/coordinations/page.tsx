"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import {
  EmergencyRequest,
  VolunteerProfile,
  Assignment,
  ReliefResource,
  Shelter,
  HealthResponse,
} from "@/types/coordination";
import {
  HeartHandshake,
  Siren,
  Users,
  Package,
  Home,
  ClipboardList,
  CheckCircle2,
  Clock,
  Activity,
  Search,
  Filter,
  RefreshCw,
  AlertTriangle,
  ServerCrash,
  ChevronRight,
  MapPin,
  ShieldAlert,
  Car,
  Stethoscope,
  Phone,
  User,
  ArrowRight,
  Database,
} from "lucide-react";

type CoordinationTab = "requests" | "volunteers" | "resources" | "assignments";

export default function CoordinationsPage() {
  const [activeTab, setActiveTab] = useState<CoordinationTab>("requests");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Live Backend Data
  const [requests, setRequests] = useState<EmergencyRequest[]>([]);
  const [volunteers, setVolunteers] = useState<VolunteerProfile[]>([]);
  const [resources, setResources] = useState<ReliefResource[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [shelters, setShelters] = useState<Shelter[]>([]);
  const [backendHealth, setBackendHealth] = useState<{ status: string; postgresql: string }>({
    status: "checking",
    postgresql: "checking",
  });

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  async function loadData(isRefresh = false) {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [
        requestsRes,
        volunteersRes,
        resourcesRes,
        assignmentsRes,
        sheltersRes,
        healthRes,
      ] = await Promise.allSettled([
        apiFetch<EmergencyRequest[]>("/api/requests?limit=100"),
        apiFetch<VolunteerProfile[]>("/api/volunteers?limit=100"),
        apiFetch<ReliefResource[]>("/api/relief-resources?limit=100"),
        apiFetch<Assignment[]>("/api/assignments?limit=100"),
        apiFetch<Shelter[]>("/api/shelters?limit=100"),
        apiFetch<HealthResponse>("/health"),
      ]);

      if (requestsRes.status === "fulfilled" && Array.isArray(requestsRes.value)) {
        setRequests(requestsRes.value);
      }
      if (volunteersRes.status === "fulfilled" && Array.isArray(volunteersRes.value)) {
        setVolunteers(volunteersRes.value);
      }
      if (resourcesRes.status === "fulfilled" && Array.isArray(resourcesRes.value)) {
        setResources(resourcesRes.value);
      }
      if (assignmentsRes.status === "fulfilled" && Array.isArray(assignmentsRes.value)) {
        setAssignments(assignmentsRes.value);
      }
      if (sheltersRes.status === "fulfilled" && Array.isArray(sheltersRes.value)) {
        setShelters(sheltersRes.value);
      }
      if (healthRes.status === "fulfilled" && healthRes.value) {
        setBackendHealth({
          status: healthRes.value.status || "healthy",
          postgresql: healthRes.value.database?.postgresql || "connected",
        });
      }
    } catch (err: any) {
      setError("Unable to connect to the coordination backend. Confirm FastAPI is running on port 8000.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  // Filtered Emergency Requests
  const filteredRequests = useMemo(() => {
    return requests.filter((r) => {
      const matchesSearch =
        !searchQuery ||
        (r.location_text && r.location_text.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (r.contact_name && r.contact_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (r.id && r.id.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesType =
        typeFilter === "all" || (r.request_type && r.request_type.toLowerCase() === typeFilter);

      const matchesStatus =
        statusFilter === "all" || (r.status && r.status.toLowerCase() === statusFilter);

      return matchesSearch && matchesType && matchesStatus;
    });
  }, [requests, searchQuery, typeFilter, statusFilter]);

  // Operational metrics
  const metrics = useMemo(() => {
    const totalRequests = requests.length;
    const pendingRequests = requests.filter((r) => r.status === "pending").length;
    const inProgressRequests = requests.filter((r) => r.status === "in_progress").length;
    const resolvedRequests = requests.filter((r) => r.status === "resolved").length;

    const totalVolunteers = volunteers.length;
    const activeVolunteers = volunteers.filter((v) => v.is_active || v.status === "active").length;

    const totalResources = resources.length;
    const availableResources = resources.filter((res) => res.status === "available" || (res.available_quantity ?? 0) > 0).length;

    const totalShelters = shelters.length;

    return {
      totalRequests,
      pendingRequests,
      inProgressRequests,
      resolvedRequests,
      totalVolunteers,
      activeVolunteers,
      totalResources,
      availableResources,
      totalShelters,
    };
  }, [requests, volunteers, resources, shelters]);

  return (
    <div style={{ maxWidth: "1280px" }}>
      {/* ── TOP HEADER ── */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "16px",
          marginBottom: "28px",
          borderBottom: "1px solid var(--line)",
          paddingBottom: "20px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span
              style={{
                font: "700 11px 'DM Mono', monospace",
                letterSpacing: "1px",
                color: "var(--accent-text)",
                textTransform: "uppercase",
              }}
            >
              DISASTER RESPONSE COMMAND
            </span>
            <span
              style={{
                fontSize: "10px",
                fontFamily: "'DM Mono'",
                fontWeight: 700,
                padding: "2px 6px",
                borderRadius: "3px",
                backgroundColor: "rgba(16, 185, 129, 0.12)",
                color: "#059669",
                border: "1px solid rgba(16, 185, 129, 0.3)",
              }}
            >
              LIVE POSTGRESQL CONNECTOR
            </span>
          </div>

          <h1
            style={{
              font: "700 clamp(24px, 4vw, 32px) 'Space Grotesk', sans-serif",
              letterSpacing: "-0.5px",
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            Coordinations
          </h1>

          <p
            style={{
              font: "400 14px/1.5 'DM Sans', sans-serif",
              color: "var(--text-secondary)",
              margin: "6px 0 0",
              maxWidth: "680px",
            }}
          >
            Real-time disaster coordination workspace connecting directly to the FastAPI coordination engine. Manage emergency requests, volunteer mobilization, resource allocations, and shelters.
          </p>
        </div>

        {/* Live Refresh and Connection Status */}
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button
            type="button"
            onClick={() => loadData(true)}
            disabled={refreshing}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 16px",
              borderRadius: "4px",
              backgroundColor: "var(--surface)",
              color: "var(--text-primary)",
              border: "1px solid var(--line)",
              font: "700 12px 'DM Mono'",
              letterSpacing: "0.5px",
              cursor: refreshing ? "wait" : "pointer",
            }}
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
            <span>{refreshing ? "SYNCHRONIZING..." : "REFRESH DATA"}</span>
          </button>
        </div>
      </div>

      {/* ── ERROR BANNER ── */}
      {error && (
        <div
          style={{
            padding: "16px 20px",
            borderRadius: "6px",
            backgroundColor: "#fee2e2",
            border: "1px solid #fecaca",
            color: "#991b1b",
            marginBottom: "28px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            font: "500 13px 'DM Sans'",
          }}
        >
          <ServerCrash size={20} style={{ flexShrink: 0 }} />
          <div>{error}</div>
        </div>
      )}

      {/* ── OPERATIONAL STAT CARDS ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
          gap: "16px",
          marginBottom: "28px",
        }}
      >
        {/* Card 1: Total Emergency Requests */}
        <div className="analytics-stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div className="analytics-stat-label">EMERGENCY REQUESTS</div>
              <div className="analytics-stat-value" style={{ color: "var(--text-primary)" }}>
                {loading ? "..." : metrics.totalRequests}
              </div>
            </div>
            <div style={{ color: "var(--accent-text)", opacity: 0.8 }}>
              <Siren size={22} />
            </div>
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "8px", fontFamily: "'DM Mono'" }}>
            {metrics.pendingRequests} pending triage
          </div>
        </div>

        {/* Card 2: Active Volunteers */}
        <div className="analytics-stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div className="analytics-stat-label">VOLUNTEERS REGISTERED</div>
              <div className="analytics-stat-value" style={{ color: "var(--green)" }}>
                {loading ? "..." : metrics.totalVolunteers}
              </div>
            </div>
            <div style={{ color: "var(--green)", opacity: 0.8 }}>
              <Users size={22} />
            </div>
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "8px", fontFamily: "'DM Mono'" }}>
            {metrics.activeVolunteers} active in field
          </div>
        </div>

        {/* Card 3: Relief Resources */}
        <div className="analytics-stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div className="analytics-stat-label">RELIEF RESOURCES</div>
              <div className="analytics-stat-value" style={{ color: "#3b82f6" }}>
                {loading ? "..." : metrics.totalResources}
              </div>
            </div>
            <div style={{ color: "#3b82f6", opacity: 0.8 }}>
              <Package size={22} />
            </div>
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "8px", fontFamily: "'DM Mono'" }}>
            {metrics.availableResources} available inventory
          </div>
        </div>

        {/* Card 4: Shelters */}
        <div className="analytics-stat-card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <div className="analytics-stat-label">ACTIVE SHELTERS</div>
              <div className="analytics-stat-value" style={{ color: "var(--amber)" }}>
                {loading ? "..." : metrics.totalShelters}
              </div>
            </div>
            <div style={{ color: "var(--amber)", opacity: 0.8 }}>
              <Home size={22} />
            </div>
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "8px", fontFamily: "'DM Mono'" }}>
            Evacuation safe-points
          </div>
        </div>
      </div>

      {/* ── COORDINATION TABS ── */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          borderBottom: "1px solid var(--line)",
          marginBottom: "24px",
          overflowX: "auto",
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab("requests")}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 18px",
            font: "700 13px 'Space Grotesk'",
            borderBottom: activeTab === "requests" ? "2.5px solid var(--accent-text)" : "2.5px solid transparent",
            color: activeTab === "requests" ? "var(--text-primary)" : "var(--text-secondary)",
            background: "transparent",
            borderTop: "none",
            borderLeft: "none",
            borderRight: "none",
            cursor: "pointer",
          }}
        >
          <Siren size={15} style={{ color: activeTab === "requests" ? "var(--accent-text)" : "inherit" }} />
          <span>Emergency Requests ({requests.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("volunteers")}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 18px",
            font: "700 13px 'Space Grotesk'",
            borderBottom: activeTab === "volunteers" ? "2.5px solid var(--accent-text)" : "2.5px solid transparent",
            color: activeTab === "volunteers" ? "var(--text-primary)" : "var(--text-secondary)",
            background: "transparent",
            borderTop: "none",
            borderLeft: "none",
            borderRight: "none",
            cursor: "pointer",
          }}
        >
          <Users size={15} style={{ color: activeTab === "volunteers" ? "var(--accent-text)" : "inherit" }} />
          <span>Volunteer Roster ({volunteers.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("resources")}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 18px",
            font: "700 13px 'Space Grotesk'",
            borderBottom: activeTab === "resources" ? "2.5px solid var(--accent-text)" : "2.5px solid transparent",
            color: activeTab === "resources" ? "var(--text-primary)" : "var(--text-secondary)",
            background: "transparent",
            borderTop: "none",
            borderLeft: "none",
            borderRight: "none",
            cursor: "pointer",
          }}
        >
          <Package size={15} style={{ color: activeTab === "resources" ? "var(--accent-text)" : "inherit" }} />
          <span>Resources &amp; Shelters ({resources.length + shelters.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("assignments")}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 18px",
            font: "700 13px 'Space Grotesk'",
            borderBottom: activeTab === "assignments" ? "2.5px solid var(--accent-text)" : "2.5px solid transparent",
            color: activeTab === "assignments" ? "var(--text-primary)" : "var(--text-secondary)",
            background: "transparent",
            borderTop: "none",
            borderLeft: "none",
            borderRight: "none",
            cursor: "pointer",
          }}
        >
          <ClipboardList size={15} style={{ color: activeTab === "assignments" ? "var(--accent-text)" : "inherit" }} />
          <span>Active Assignments ({assignments.length})</span>
        </button>
      </div>

      {/* ── TAB 1: EMERGENCY REQUESTS ── */}
      {activeTab === "requests" && (
        <div>
          {/* Search and Filters Bar */}
          <div
            style={{
              display: "flex",
              gap: "12px",
              flexWrap: "wrap",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: "20px",
            }}
          >
            <div style={{ display: "flex", gap: "10px", flex: 1, minWidth: "260px" }}>
              <div
                style={{
                  position: "relative",
                  flex: 1,
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <Search
                  size={15}
                  style={{ position: "absolute", left: "12px", color: "var(--text-secondary)" }}
                />
                <input
                  type="text"
                  placeholder="Search requests by location, contact name, or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "9px 12px 9px 36px",
                    borderRadius: "4px",
                    border: "1px solid var(--line)",
                    backgroundColor: "var(--surface)",
                    color: "var(--text-primary)",
                    font: "400 13px 'DM Sans'",
                  }}
                />
              </div>

              {/* Type Filter */}
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                style={{
                  padding: "9px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  backgroundColor: "var(--surface)",
                  color: "var(--text-primary)",
                  font: "600 12px 'DM Mono'",
                }}
              >
                <option value="all">ALL TYPES</option>
                <option value="relief">RELIEF</option>
                <option value="evacuation">EVACUATION</option>
                <option value="help">HELP</option>
              </select>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  padding: "9px 12px",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  backgroundColor: "var(--surface)",
                  color: "var(--text-primary)",
                  font: "600 12px 'DM Mono'",
                }}
              >
                <option value="all">ALL STATUSES</option>
                <option value="pending">PENDING</option>
                <option value="in_progress">IN PROGRESS</option>
                <option value="resolved">RESOLVED</option>
              </select>
            </div>
          </div>

          {/* Table Container */}
          <div
            className="card"
            style={{
              padding: 0,
              overflow: "hidden",
              border: "1px solid var(--line)",
              borderRadius: "6px",
            }}
          >
            {loading ? (
              <div style={{ padding: "40px", textAlign: "center", color: "var(--text-secondary)" }}>
                <RefreshCw size={24} className="animate-spin" style={{ margin: "0 auto 12px" }} />
                <p style={{ font: "500 13px 'DM Mono'", margin: 0 }}>FETCHING LIVE EMERGENCY REQUESTS...</p>
              </div>
            ) : filteredRequests.length === 0 ? (
              <div style={{ padding: "48px 24px", textAlign: "center", color: "var(--text-secondary)" }}>
                <Siren size={32} style={{ margin: "0 auto 12px", opacity: 0.4 }} />
                <p style={{ font: "700 14px 'Space Grotesk'", color: "var(--text-primary)", margin: "0 0 6px" }}>
                  No Emergency Requests Found
                </p>
                <p style={{ font: "400 13px 'DM Sans'", margin: 0 }}>
                  {searchQuery || typeFilter !== "all" || statusFilter !== "all"
                    ? "Try adjusting your search criteria or filters."
                    : "No emergency requests have been registered in the database yet."}
                </p>
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                  <thead>
                    <tr
                      style={{
                        backgroundColor: "rgba(0,0,0,0.03)",
                        borderBottom: "1px solid var(--line)",
                        textAlign: "left",
                        fontFamily: "'DM Mono', monospace",
                        fontSize: "11px",
                        letterSpacing: "0.5px",
                        color: "var(--text-secondary)",
                      }}
                    >
                      <th style={{ padding: "12px 16px" }}>REQUEST TYPE</th>
                      <th style={{ padding: "12px 16px" }}>LOCATION</th>
                      <th style={{ padding: "12px 16px" }}>SEVERITY</th>
                      <th style={{ padding: "12px 16px" }}>AFFECTED</th>
                      <th style={{ padding: "12px 16px" }}>CONTACT</th>
                      <th style={{ padding: "12px 16px" }}>STATUS</th>
                      <th style={{ padding: "12px 16px" }}>TIMESTAMP</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRequests.map((req) => {
                      const isHigh = req.severity === "high" || req.severity === "critical";
                      return (
                        <tr
                          key={req.id}
                          style={{
                            borderBottom: "1px solid var(--line)",
                            transition: "background-color 0.15s ease",
                          }}
                        >
                          <td style={{ padding: "12px 16px" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                              {req.request_type === "evacuation" ? (
                                <Car size={15} style={{ color: "#3b82f6" }} />
                              ) : req.request_type === "relief" ? (
                                <Stethoscope size={15} style={{ color: "var(--amber)" }} />
                              ) : (
                                <Siren size={15} style={{ color: "var(--accent-text)" }} />
                              )}
                              <span
                                style={{
                                  fontFamily: "'DM Mono', monospace",
                                  fontWeight: 700,
                                  fontSize: "11px",
                                  textTransform: "uppercase",
                                }}
                              >
                                {req.request_type}
                              </span>
                            </div>
                          </td>

                          <td style={{ padding: "12px 16px", color: "var(--text-primary)" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              <MapPin size={13} style={{ color: "var(--text-secondary)", flexShrink: 0 }} />
                              <span style={{ fontWeight: 500 }}>
                                {req.location_text || "Unspecified Location"}
                              </span>
                            </div>
                          </td>

                          <td style={{ padding: "12px 16px" }}>
                            <span
                              style={{
                                fontSize: "10px",
                                fontFamily: "'DM Mono'",
                                fontWeight: 700,
                                padding: "2px 6px",
                                borderRadius: "3px",
                                textTransform: "uppercase",
                                backgroundColor: isHigh ? "rgba(220, 38, 38, 0.12)" : "rgba(210, 153, 34, 0.12)",
                                color: isHigh ? "#dc2626" : "#b45309",
                                border: isHigh ? "1px solid rgba(220, 38, 38, 0.3)" : "1px solid rgba(210, 153, 34, 0.3)",
                              }}
                            >
                              {req.severity || "NORMAL"}
                            </span>
                          </td>

                          <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'", fontWeight: 600 }}>
                            {req.people_affected ? `${req.people_affected} people` : "—"}
                          </td>

                          <td style={{ padding: "12px 16px" }}>
                            <div style={{ display: "flex", flexDirection: "column", fontSize: "12px" }}>
                              <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                                {req.contact_name || "Anonymous"}
                              </span>
                              {req.contact_phone && (
                                <span style={{ color: "var(--text-secondary)", fontFamily: "'DM Mono'", fontSize: "11px" }}>
                                  {req.contact_phone}
                                </span>
                              )}
                            </div>
                          </td>

                          <td style={{ padding: "12px 16px" }}>
                            <span
                              style={{
                                fontSize: "11px",
                                fontFamily: "'DM Mono'",
                                fontWeight: 700,
                                textTransform: "uppercase",
                                color:
                                  req.status === "resolved"
                                    ? "var(--green)"
                                    : req.status === "in_progress"
                                    ? "#3b82f6"
                                    : "var(--amber)",
                              }}
                            >
                              &bull; {req.status}
                            </span>
                          </td>

                          <td
                            style={{
                              padding: "12px 16px",
                              fontFamily: "'DM Mono'",
                              fontSize: "11px",
                              color: "var(--text-secondary)",
                            }}
                          >
                            {req.created_at ? new Date(req.created_at).toLocaleString() : "—"}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TAB 2: VOLUNTEERS ── */}
      {activeTab === "volunteers" && (
        <div
          className="card"
          style={{
            padding: 0,
            overflow: "hidden",
            border: "1px solid var(--line)",
            borderRadius: "6px",
          }}
        >
          {loading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "var(--text-secondary)" }}>
              <RefreshCw size={24} className="animate-spin" style={{ margin: "0 auto 12px" }} />
              <p style={{ font: "500 13px 'DM Mono'", margin: 0 }}>LOADING REGISTERED VOLUNTEER ROSTERS...</p>
            </div>
          ) : volunteers.length === 0 ? (
            <div style={{ padding: "48px 24px", textAlign: "center", color: "var(--text-secondary)" }}>
              <Users size={32} style={{ margin: "0 auto 12px", opacity: 0.4 }} />
              <p style={{ font: "700 14px 'Space Grotesk'", color: "var(--text-primary)", margin: 0 }}>
                No Volunteer Profiles Recorded
              </p>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                <thead>
                  <tr
                    style={{
                      backgroundColor: "rgba(0,0,0,0.03)",
                      borderBottom: "1px solid var(--line)",
                      textAlign: "left",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "11px",
                      letterSpacing: "0.5px",
                      color: "var(--text-secondary)",
                    }}
                  >
                    <th style={{ padding: "12px 16px" }}>VOLUNTEER ID</th>
                    <th style={{ padding: "12px 16px" }}>SKILLS</th>
                    <th style={{ padding: "12px 16px" }}>TRANSPORT</th>
                    <th style={{ padding: "12px 16px" }}>CAPACITY</th>
                    <th style={{ padding: "12px 16px" }}>AVAILABILITY</th>
                    <th style={{ padding: "12px 16px" }}>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {volunteers.map((vol) => (
                    <tr key={vol.id} style={{ borderBottom: "1px solid var(--line)" }}>
                      <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'", fontSize: "11px" }}>
                        {vol.id.substring(0, 8)}...
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                          {vol.skills && vol.skills.length > 0 ? (
                            vol.skills.map((s) => (
                              <span
                                key={s}
                                style={{
                                  fontSize: "10px",
                                  fontFamily: "'DM Mono'",
                                  padding: "2px 6px",
                                  borderRadius: "3px",
                                  backgroundColor: "var(--surface)",
                                  border: "1px solid var(--line)",
                                }}
                              >
                                {s}
                              </span>
                            ))
                          ) : (
                            <span style={{ color: "var(--text-secondary)" }}>General assistance</span>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        {vol.has_transport ? (
                          <span style={{ color: "var(--green)", fontWeight: 600 }}>Vehicle Available</span>
                        ) : (
                          <span style={{ color: "var(--text-secondary)" }}>On Foot</span>
                        )}
                      </td>
                      <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'", fontWeight: 600 }}>
                        {vol.capacity ?? "—"}
                      </td>
                      <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>
                        {vol.availability || "Flexible"}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span
                          style={{
                            fontSize: "11px",
                            fontFamily: "'DM Mono'",
                            fontWeight: 700,
                            color: vol.status === "active" ? "var(--green)" : "var(--amber)",
                            textTransform: "uppercase",
                          }}
                        >
                          &bull; {vol.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── TAB 3: RELIEF RESOURCES & SHELTERS ── */}
      {activeTab === "resources" && (
        <div style={{ display: "grid", gap: "24px" }}>
          {/* Resources Table */}
          <div
            className="card"
            style={{
              padding: 0,
              overflow: "hidden",
              border: "1px solid var(--line)",
              borderRadius: "6px",
            }}
          >
            <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--line)", backgroundColor: "var(--surface)" }}>
              <h3 style={{ font: "700 15px 'Space Grotesk'", margin: 0, color: "var(--text-primary)" }}>
                Relief Supplies Inventory ({resources.length})
              </h3>
            </div>
            {resources.length === 0 ? (
              <div style={{ padding: "32px", textAlign: "center", color: "var(--text-secondary)" }}>
                No relief resources recorded in database.
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                  <thead>
                    <tr
                      style={{
                        backgroundColor: "rgba(0,0,0,0.03)",
                        borderBottom: "1px solid var(--line)",
                        textAlign: "left",
                        fontFamily: "'DM Mono', monospace",
                        fontSize: "11px",
                        letterSpacing: "0.5px",
                        color: "var(--text-secondary)",
                      }}
                    >
                      <th style={{ padding: "12px 16px" }}>TYPE</th>
                      <th style={{ padding: "12px 16px" }}>DESCRIPTION</th>
                      <th style={{ padding: "12px 16px" }}>TOTAL QTY</th>
                      <th style={{ padding: "12px 16px" }}>AVAILABLE</th>
                      <th style={{ padding: "12px 16px" }}>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resources.map((res) => (
                      <tr key={res.id} style={{ borderBottom: "1px solid var(--line)" }}>
                        <td style={{ padding: "12px 16px", fontWeight: 600, textTransform: "capitalize" }}>
                          {res.resource_type}
                        </td>
                        <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>
                          {res.description || "—"}
                        </td>
                        <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'", fontWeight: 600 }}>
                          {res.quantity} {res.unit}
                        </td>
                        <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'", fontWeight: 700, color: "var(--green)" }}>
                          {res.available_quantity ?? res.quantity} {res.unit}
                        </td>
                        <td style={{ padding: "12px 16px" }}>
                          <span style={{ fontSize: "11px", fontFamily: "'DM Mono'", fontWeight: 700, textTransform: "uppercase" }}>
                            {res.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Shelters Table */}
          <div
            className="card"
            style={{
              padding: 0,
              overflow: "hidden",
              border: "1px solid var(--line)",
              borderRadius: "6px",
            }}
          >
            <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--line)", backgroundColor: "var(--surface)" }}>
              <h3 style={{ font: "700 15px 'Space Grotesk'", margin: 0, color: "var(--text-primary)" }}>
                Emergency Evacuation Shelters ({shelters.length})
              </h3>
            </div>
            {shelters.length === 0 ? (
              <div style={{ padding: "32px", textAlign: "center", color: "var(--text-secondary)" }}>
                No emergency shelters registered in database.
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                  <thead>
                    <tr
                      style={{
                        backgroundColor: "rgba(0,0,0,0.03)",
                        borderBottom: "1px solid var(--line)",
                        textAlign: "left",
                        fontFamily: "'DM Mono', monospace",
                        fontSize: "11px",
                        letterSpacing: "0.5px",
                        color: "var(--text-secondary)",
                      }}
                    >
                      <th style={{ padding: "12px 16px" }}>SHELTER NAME</th>
                      <th style={{ padding: "12px 16px" }}>ADDRESS</th>
                      <th style={{ padding: "12px 16px" }}>CAPACITY</th>
                      <th style={{ padding: "12px 16px" }}>OCCUPANCY</th>
                      <th style={{ padding: "12px 16px" }}>CONTACT</th>
                      <th style={{ padding: "12px 16px" }}>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {shelters.map((sh) => (
                      <tr key={sh.id} style={{ borderBottom: "1px solid var(--line)" }}>
                        <td style={{ padding: "12px 16px", fontWeight: 600 }}>{sh.name}</td>
                        <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>{sh.address || "—"}</td>
                        <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'" }}>{sh.capacity} persons</td>
                        <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'", fontWeight: 700 }}>
                          {sh.current_occupancy} / {sh.capacity}
                        </td>
                        <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'", fontSize: "11px" }}>
                          {sh.contact_phone || "—"}
                        </td>
                        <td style={{ padding: "12px 16px" }}>
                          <span style={{ fontSize: "11px", fontFamily: "'DM Mono'", fontWeight: 700, textTransform: "uppercase" }}>
                            {sh.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── TAB 4: ASSIGNMENTS ── */}
      {activeTab === "assignments" && (
        <div
          className="card"
          style={{
            padding: 0,
            overflow: "hidden",
            border: "1px solid var(--line)",
            borderRadius: "6px",
          }}
        >
          {assignments.length === 0 ? (
            <div style={{ padding: "48px 24px", textAlign: "center", color: "var(--text-secondary)" }}>
              <ClipboardList size={32} style={{ margin: "0 auto 12px", opacity: 0.4 }} />
              <p style={{ font: "700 14px 'Space Grotesk'", color: "var(--text-primary)", margin: 0 }}>
                No Active Resource or Volunteer Assignments
              </p>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                <thead>
                  <tr
                    style={{
                      backgroundColor: "rgba(0,0,0,0.03)",
                      borderBottom: "1px solid var(--line)",
                      textAlign: "left",
                      fontFamily: "'DM Mono', monospace",
                      fontSize: "11px",
                      letterSpacing: "0.5px",
                      color: "var(--text-secondary)",
                    }}
                  >
                    <th style={{ padding: "12px 16px" }}>ASSIGNMENT ID</th>
                    <th style={{ padding: "12px 16px" }}>TYPE</th>
                    <th style={{ padding: "12px 16px" }}>STATUS</th>
                    <th style={{ padding: "12px 16px" }}>NOTES</th>
                    <th style={{ padding: "12px 16px" }}>ASSIGNED AT</th>
                  </tr>
                </thead>
                <tbody>
                  {assignments.map((asg) => (
                    <tr key={asg.id} style={{ borderBottom: "1px solid var(--line)" }}>
                      <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'", fontSize: "11px" }}>
                        {asg.id.substring(0, 8)}...
                      </td>
                      <td style={{ padding: "12px 16px", fontWeight: 600, textTransform: "uppercase" }}>
                        {asg.assignment_type}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span style={{ fontSize: "11px", fontFamily: "'DM Mono'", fontWeight: 700, textTransform: "uppercase" }}>
                          &bull; {asg.status}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px", color: "var(--text-secondary)" }}>{asg.notes || "—"}</td>
                      <td style={{ padding: "12px 16px", fontFamily: "'DM Mono'", fontSize: "11px", color: "var(--text-secondary)" }}>
                        {asg.created_at ? new Date(asg.created_at).toLocaleString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
