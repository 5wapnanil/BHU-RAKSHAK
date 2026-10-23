"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { FieldReport, ReviewStatus, HazardLevel } from "@/types/fieldReport";
import { fetchFieldReportById, updateFieldReportStatus, triggerFieldReportAnalysis } from "@/lib/fieldReports";
import {
  ArrowLeft,
  MapPin,
  Clock,
  User,
  Phone,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Cpu,
  AlertTriangle,
  FileText,
  Image as ImageIcon,
  Save,
  Check,
  ExternalLink,
  Map,
  CornerDownRight,
  Info,
  Sparkles,
  RefreshCw,
} from "lucide-react";

export default function FieldReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = typeof params?.id === "string" ? params.id : Array.isArray(params?.id) ? params.id[0] : "";

  const [report, setReport] = useState<FieldReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review console states
  const [selectedStatus, setSelectedStatus] = useState<ReviewStatus>("pending");
  const [adminNotes, setAdminNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // AI analysis trigger states
  const [analyzing, setAnalyzing] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiSuccess, setAiSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    async function loadReport() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchFieldReportById(id);
        if (cancelled) return;
        if (!data) {
          setError("Report not found or has been removed from central records.");
        } else {
          setReport(data);
          setSelectedStatus(data.review_status);
          setAdminNotes(data.admin_notes || "");
        }
      } catch (err: any) {
        if (!cancelled) {
          setError("Unable to reach backend API. Please confirm FastAPI is active.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadReport();
    return () => {
      cancelled = true;
    };
  }, [id]);

  async function handleSaveDecision() {
    if (!report) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const res = await updateFieldReportStatus(report.id, selectedStatus, adminNotes);
      if (res.success) {
        setSaveSuccess(true);
        setReport({
          ...report,
          review_status: selectedStatus,
          admin_notes: adminNotes,
          reviewed_at: new Date().toISOString(),
          reviewed_by: null,
        });
        setTimeout(() => setSaveSuccess(false), 4000);
      } else {
        setSaveError(res.error || "Failed to save review decision to central database.");
      }
    } catch (err: any) {
      setSaveError(err.message || "Failed to update review status");
    } finally {
      setSaving(false);
    }
  }

  async function handleTriggerAnalysis(force = true) {
    if (!report) return;
    setAnalyzing(true);
    setAiError(null);
    setAiSuccess(null);
    try {
      const res = await triggerFieldReportAnalysis(report.id, force);
      if (res.success && res.data) {
        setReport(res.data);
        setAiSuccess("AI preliminary hazard screening updated successfully.");
        setTimeout(() => setAiSuccess(null), 4000);
      } else {
        setAiError(res.error || "Failed to complete AI hazard screening.");
      }
    } catch (err: any) {
      setAiError(err?.message || "Unexpected error triggering AI screening.");
    } finally {
      setAnalyzing(false);
    }
  }

  const HAZARD_LABELS: Record<string, string> = {
    tension_cracks: "Tension Cracks",
    slope_displacement: "Slope Displacement",
    road_blockage: "Road Blockage",
    water_seepage: "Water Seepage",
    soil_erosion: "Soil Erosion",
    mudflow: "Mudflow / Debris Flow",
    structural_damage: "Structural Damage",
    rockfall: "Rockfall Hazard",
    drainage_compromised: "Compromised Drainage",
  };

  function renderStatusBadge(status: ReviewStatus) {
    switch (status) {
      case "verified":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "5px",
              padding: "4px 10px",
              borderRadius: "4px",
              fontSize: "12px",
              fontFamily: "'DM Mono', monospace",
              fontWeight: 700,
              backgroundColor: "rgba(16, 185, 129, 0.12)",
              color: "#059669",
              border: "1px solid rgba(16, 185, 129, 0.3)",
            }}
          >
            <CheckCircle2 size={13} />
            VERIFIED
          </span>
        );
      case "under_review":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "5px",
              padding: "4px 10px",
              borderRadius: "4px",
              fontSize: "12px",
              fontFamily: "'DM Mono', monospace",
              fontWeight: 700,
              backgroundColor: "rgba(245, 158, 11, 0.12)",
              color: "#d97706",
              border: "1px solid rgba(245, 158, 11, 0.3)",
            }}
          >
            <Clock size={13} />
            UNDER REVIEW
          </span>
        );
      case "rejected":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "5px",
              padding: "4px 10px",
              borderRadius: "4px",
              fontSize: "12px",
              fontFamily: "'DM Mono', monospace",
              fontWeight: 700,
              backgroundColor: "rgba(239, 68, 68, 0.12)",
              color: "#dc2626",
              border: "1px solid rgba(239, 68, 68, 0.3)",
            }}
          >
            <XCircle size={13} />
            REJECTED
          </span>
        );
      default:
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "5px",
              padding: "4px 10px",
              borderRadius: "4px",
              fontSize: "12px",
              fontFamily: "'DM Mono', monospace",
              fontWeight: 700,
              backgroundColor: "rgba(100, 116, 139, 0.12)",
              color: "var(--text-secondary)",
              border: "1px solid var(--line)",
            }}
          >
            <HelpCircle size={13} />
            AWAITING REVIEW
          </span>
        );
    }
  }

  if (loading) {
    return (
      <div style={{ maxWidth: "1200px", padding: "40px 0", textAlign: "center" }}>
        <p style={{ font: "500 15px 'DM Sans'", color: "var(--text-secondary)" }}>
          Loading field report details...
        </p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ maxWidth: "900px", margin: "20px auto" }}>
        <div
          className="card"
          style={{
            padding: "36px",
            textAlign: "center",
            borderLeft: "4px solid #ef4444",
          }}
        >
          <AlertTriangle size={36} color="#dc2626" style={{ margin: "0 auto 12px" }} />
          <h2 style={{ font: "700 20px 'Space Grotesk'", color: "var(--text-primary)", margin: "0 0 8px" }}>
            Report Unavailable
          </h2>
          <p style={{ font: "400 14px 'DM Sans'", color: "var(--text-secondary)", marginBottom: "20px" }}>
            {error || "Could not retrieve the specified field report."}
          </p>
          <Link
            href="/dashboard/reports"
            className="btn btn-primary"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 16px",
            }}
          >
            <ArrowLeft size={14} /> Back to Field Reports
          </Link>
        </div>
      </div>
    );
  }

  const formattedDate = new Date(report.submitted_at).toLocaleDateString("en-IN", {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div style={{ maxWidth: "1280px", paddingBottom: "60px" }}>
      {/* Breadcrumb & Navigation */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Link
            href="/dashboard/reports"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "13px",
              fontFamily: "'DM Sans', sans-serif",
              color: "var(--text-secondary)",
              textDecoration: "none",
            }}
            className="hover:text-[var(--text-primary)]"
          >
            <ArrowLeft size={14} /> Field Reports
          </Link>
          <span style={{ color: "var(--line)" }}>/</span>
          <span style={{ fontFamily: "'DM Mono', monospace", fontSize: "12px", color: "var(--text-primary)", fontWeight: 700 }}>
            #{report.id.slice(0, 8)}
          </span>
        </div>

        {typeof report.latitude === "number" && typeof report.longitude === "number" && (
          <Link
            href="/dashboard/map"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "12px",
              fontFamily: "'DM Sans', sans-serif",
              fontWeight: 600,
              color: "var(--accent-text)",
              padding: "6px 12px",
              borderRadius: "4px",
              border: "1px solid var(--line)",
              backgroundColor: "var(--surface)",
              textDecoration: "none",
            }}
          >
            <Map size={13} />
            View Coordinates on Map
          </Link>
        )}
      </div>

      {/* Report Header Title Card */}
      <div
        className="card"
        style={{
          padding: "24px",
          marginBottom: "24px",
          borderTop: "3px solid var(--accent-text)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <span
                style={{
                  fontFamily: "'DM Mono', monospace",
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "var(--accent-text)",
                }}
              >
                REPORT #{report.id}
              </span>
              {renderStatusBadge(report.review_status)}
            </div>
            <h1
              style={{
                font: "700 clamp(22px, 3.5vw, 28px) 'Space Grotesk'",
                letterSpacing: "-0.5px",
                color: "var(--text-primary)",
                margin: "0 0 6px",
              }}
            >
              {report.location_name}
            </h1>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "16px",
                fontSize: "12px",
                fontFamily: "'DM Mono', monospace",
                color: "var(--text-secondary)",
              }}
            >
              <span style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}>
                <Clock size={13} />
                Submitted {formattedDate}
              </span>
              {report.client_op_id && (
                <span style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}>
                  <CornerDownRight size={13} />
                  Op ID: {report.client_op_id}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Two-Column Grid: Left (Evidence & Ground Data) / Right (AI & Adjudication) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
          gap: "24px",
          alignItems: "start",
        }}
      >
        {/* LEFT COLUMN: Field Evidence & Observation */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Photo Evidence Box */}
          <div className="card" style={{ padding: "20px" }}>
            <h3
              style={{
                font: "700 13px 'DM Mono'",
                letterSpacing: "0.5px",
                color: "var(--text-secondary)",
                margin: "0 0 14px",
                textTransform: "uppercase",
              }}
            >
              Field Photo Evidence
            </h3>

            {report.photo_url ? (
              <div
                style={{
                  borderRadius: "6px",
                  overflow: "hidden",
                  border: "1px solid var(--line)",
                  backgroundColor: "#000",
                }}
              >
                <img
                  src={report.photo_url}
                  alt="Field Evidence"
                  style={{
                    width: "100%",
                    maxHeight: "360px",
                    objectFit: "contain",
                    display: "block",
                  }}
                />
              </div>
            ) : (
              <div
                style={{
                  padding: "40px 20px",
                  textAlign: "center",
                  borderRadius: "6px",
                  border: "1px dashed var(--line)",
                  backgroundColor: "var(--paper)",
                }}
              >
                <ImageIcon
                  size={36}
                  style={{ color: "var(--text-secondary)", margin: "0 auto 10px", opacity: 0.5 }}
                />
                <p
                  style={{
                    font: "600 13px 'Space Grotesk'",
                    color: "var(--text-primary)",
                    margin: "0 0 4px",
                  }}
                >
                  No photographic asset attached
                </p>
                <p
                  style={{
                    font: "400 12px 'DM Sans'",
                    color: "var(--text-secondary)",
                    margin: 0,
                  }}
                >
                  The reporter submitted observational notes without an accompanying field photo.
                </p>
              </div>
            )}
          </div>

          {/* Observation Notes Card */}
          <div className="card" style={{ padding: "20px" }}>
            <h3
              style={{
                font: "700 13px 'DM Mono'",
                letterSpacing: "0.5px",
                color: "var(--text-secondary)",
                margin: "0 0 12px",
                textTransform: "uppercase",
              }}
            >
              Observation Notes
            </h3>
            <div
              style={{
                padding: "16px",
                borderRadius: "6px",
                backgroundColor: "var(--surface)",
                border: "1px solid var(--line)",
                font: "400 14px/1.6 'DM Sans'",
                color: "var(--text-primary)",
                whiteSpace: "pre-wrap",
              }}
            >
              {report.notes}
            </div>
          </div>

          {/* Location & GPS Card */}
          <div className="card" style={{ padding: "20px" }}>
            <h3
              style={{
                font: "700 13px 'DM Mono'",
                letterSpacing: "0.5px",
                color: "var(--text-secondary)",
                margin: "0 0 12px",
                textTransform: "uppercase",
              }}
            >
              Landmark &amp; Geolocation
            </h3>

            <div style={{ display: "grid", gap: "10px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "10px 12px",
                  borderRadius: "4px",
                  backgroundColor: "var(--surface)",
                  border: "1px solid var(--line)",
                }}
              >
                <span style={{ font: "500 12px 'DM Sans'", color: "var(--text-secondary)" }}>
                  Landmark Sector
                </span>
                <span
                  style={{
                    font: "600 13px 'Space Grotesk'",
                    color: "var(--text-primary)",
                  }}
                >
                  {report.location_name}
                </span>
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "10px 12px",
                  borderRadius: "4px",
                  backgroundColor: "var(--surface)",
                  border: "1px solid var(--line)",
                }}
              >
                <span style={{ font: "500 12px 'DM Sans'", color: "var(--text-secondary)" }}>
                  GPS Coordinates
                </span>
                <span
                  style={{
                    font: "700 12px 'DM Mono'",
                    color:
                      typeof report.latitude === "number" && typeof report.longitude === "number"
                        ? "var(--accent-text)"
                        : "var(--text-secondary)",
                  }}
                >
                  {typeof report.latitude === "number" && typeof report.longitude === "number"
                    ? `${report.latitude.toFixed(5)}° N, ${report.longitude.toFixed(5)}° E`
                    : "Not Recorded"}
                </span>
              </div>
            </div>
          </div>

          {/* Reporter Details */}
          <div className="card" style={{ padding: "20px" }}>
            <h3
              style={{
                font: "700 13px 'DM Mono'",
                letterSpacing: "0.5px",
                color: "var(--text-secondary)",
                margin: "0 0 12px",
                textTransform: "uppercase",
              }}
            >
              Reporter Information
            </h3>

            <div style={{ display: "grid", gap: "10px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "10px 12px",
                  borderRadius: "4px",
                  backgroundColor: "var(--surface)",
                  border: "1px solid var(--line)",
                }}
              >
                <User size={15} color="var(--text-secondary)" />
                <span style={{ font: "600 13px 'DM Sans'", color: "var(--text-primary)" }}>
                  {report.reporter_name || "Anonymous Scout"}
                </span>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "10px 12px",
                  borderRadius: "4px",
                  backgroundColor: "var(--surface)",
                  border: "1px solid var(--line)",
                }}
              >
                <Phone size={15} color="var(--text-secondary)" />
                <span style={{ font: "600 13px 'DM Mono'", color: "var(--text-primary)" }}>
                  {report.reporter_phone || "No direct phone provided"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: AI Preliminary Screening & Decision Console */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* AI Preliminary Screening Card */}
          <div
            className="card"
            style={{
              padding: "22px",
              border: "1px solid rgba(224, 90, 58, 0.3)",
              background: "linear-gradient(180deg, var(--card) 0%, rgba(224, 90, 58, 0.03) 100%)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "14px",
                flexWrap: "wrap",
                gap: "8px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <Cpu size={18} color="var(--accent-text)" />
                <h3
                  style={{
                    font: "700 14px 'Space Grotesk'",
                    color: "var(--text-primary)",
                    margin: 0,
                  }}
                >
                  Preliminary AI Hazard Screening
                </h3>
              </div>
              <span
                style={{
                  padding: "3px 8px",
                  borderRadius: "10px",
                  fontSize: "10px",
                  fontFamily: "'DM Mono', monospace",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  backgroundColor:
                    (report.ai_status || report.ai_screening_status) === "completed"
                      ? "rgba(16, 185, 129, 0.15)"
                      : (report.ai_status || report.ai_screening_status) === "processing"
                      ? "rgba(59, 130, 246, 0.15)"
                      : (report.ai_status || report.ai_screening_status) === "failed"
                      ? "rgba(239, 68, 68, 0.15)"
                      : (report.ai_status || report.ai_screening_status) === "unavailable"
                      ? "rgba(245, 158, 11, 0.15)"
                      : "rgba(100, 116, 139, 0.15)",
                  color:
                    (report.ai_status || report.ai_screening_status) === "completed"
                      ? "#10b981"
                      : (report.ai_status || report.ai_screening_status) === "processing"
                      ? "#3b82f6"
                      : (report.ai_status || report.ai_screening_status) === "failed"
                      ? "#ef4444"
                      : (report.ai_status || report.ai_screening_status) === "unavailable"
                      ? "#f59e0b"
                      : "var(--text-secondary)",
                  border: "1px solid var(--line)",
                }}
              >
                {(report.ai_status || report.ai_screening_status) === "completed"
                  ? "Screening Complete"
                  : (report.ai_status || report.ai_screening_status) === "processing"
                  ? "Analyzing..."
                  : (report.ai_status || report.ai_screening_status) === "failed"
                  ? "Screening Failed"
                  : (report.ai_status || report.ai_screening_status) === "unavailable"
                  ? report.ai_summary?.toLowerCase().includes("not configured")
                    ? "Provider Unconfigured"
                    : "Temporarily Unavailable"
                  : "Awaiting Analysis"}
              </span>
            </div>

            {/* Model & Multimodal Pipeline Tag */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "8px 12px",
                borderRadius: "4px",
                backgroundColor: "var(--surface)",
                border: "1px solid var(--line)",
                marginBottom: "14px",
                fontSize: "11px",
                fontFamily: "'DM Mono', monospace",
              }}
            >
              <span style={{ color: "var(--text-secondary)" }}>PIPELINE</span>
              <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>
                Gemma {report.photo_url ? "Multimodal (Vision + Notes)" : "Text-Only (Notes Screening)"}
              </span>
            </div>

            {/* Hazard Level & Confidence Banner */}
            <div
              style={{
                padding: "14px",
                borderRadius: "6px",
                backgroundColor:
                  report.ai_hazard_level === "critical"
                    ? "rgba(239, 68, 68, 0.1)"
                    : report.ai_hazard_level === "high"
                    ? "rgba(249, 115, 22, 0.1)"
                    : report.ai_hazard_level === "moderate"
                    ? "rgba(245, 158, 11, 0.1)"
                    : report.ai_hazard_level === "low"
                    ? "rgba(16, 185, 129, 0.1)"
                    : "rgba(100, 116, 139, 0.08)",
                border:
                  report.ai_hazard_level === "critical"
                    ? "1px solid rgba(239, 68, 68, 0.35)"
                    : report.ai_hazard_level === "high"
                    ? "1px solid rgba(249, 115, 22, 0.35)"
                    : report.ai_hazard_level === "moderate"
                    ? "1px solid rgba(245, 158, 11, 0.35)"
                    : report.ai_hazard_level === "low"
                    ? "1px solid rgba(16, 185, 129, 0.35)"
                    : "1px solid var(--line)",
                marginBottom: "14px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                <span style={{ fontSize: "11px", fontFamily: "'DM Mono'", color: "var(--text-secondary)", letterSpacing: "0.5px" }}>
                  PRELIMINARY HAZARD LEVEL
                </span>
                <span
                  style={{
                    fontSize: "14px",
                    fontFamily: "'DM Mono'",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    color:
                      report.ai_hazard_level === "critical"
                        ? "#dc2626"
                        : report.ai_hazard_level === "high"
                        ? "#ea580c"
                        : report.ai_hazard_level === "moderate"
                        ? "#d97706"
                        : report.ai_hazard_level === "low"
                        ? "#16a34a"
                        : (report.ai_status || report.ai_screening_status) === "unavailable"
                        ? "#d97706"
                        : "var(--text-secondary)",
                  }}
                >
                  {(report.ai_status || report.ai_screening_status) === "unavailable"
                    ? "UNAVAILABLE"
                    : (report.ai_hazard_level || "Indeterminate")}
                </span>
              </div>

              <div style={{ marginTop: "8px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", fontFamily: "'DM Mono'", color: "var(--text-secondary)", marginBottom: "4px" }}>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
                    <span>Model-reported confidence</span>
                    <span
                      style={{
                        fontSize: "9px",
                        fontWeight: 600,
                        padding: "1px 5px",
                        borderRadius: "3px",
                        backgroundColor: "var(--surface)",
                        border: "1px solid var(--line)",
                        color: "var(--text-secondary)",
                        letterSpacing: "0.4px",
                        textTransform: "uppercase",
                      }}
                    >
                      Uncalibrated
                    </span>
                  </span>
                  <span>
                    {typeof report.ai_confidence === "number"
                      ? `${Math.round(report.ai_confidence * 100)}%`
                      : "Unavailable"}
                  </span>
                </div>
                {typeof report.ai_confidence === "number" && (
                  <div style={{ width: "100%", height: "4px", backgroundColor: "var(--line)", borderRadius: "2px", overflow: "hidden" }}>
                    <div
                      style={{
                        width: `${Math.min(100, Math.max(0, Math.round(report.ai_confidence * 100)))}%`,
                        height: "100%",
                        backgroundColor:
                          report.ai_hazard_level === "critical" ? "#dc2626" : "var(--accent-text)",
                        borderRadius: "2px",
                      }}
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Detected Hazards Tags */}
            <div style={{ marginBottom: "14px" }}>
              <span style={{ display: "block", fontSize: "11px", fontFamily: "'DM Mono'", color: "var(--text-secondary)", marginBottom: "6px" }}>
                IDENTIFIED GEOTECHNICAL INDICATORS
              </span>
              {report.ai_analyzed_at && Array.isArray(report.ai_detected_hazards) && report.ai_detected_hazards.length > 0 ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {report.ai_detected_hazards.map((hazard, idx) => (
                    <span
                      key={idx}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                        padding: "3px 8px",
                        borderRadius: "4px",
                        fontSize: "11px",
                        fontFamily: "'DM Mono', monospace",
                        fontWeight: 600,
                        backgroundColor: "var(--surface)",
                        border: "1px solid var(--line)",
                        color: "var(--text-primary)",
                      }}
                    >
                      <AlertTriangle size={11} color="var(--accent-text)" />
                      {HAZARD_LABELS[hazard] || hazard.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              ) : (
                <p style={{ font: "400 12px 'DM Sans'", color: "var(--text-secondary)", margin: 0, fontStyle: "italic" }}>
                  {(report.ai_status || report.ai_screening_status) === "unavailable"
                    ? "Screening indicators unavailable — retry later."
                    : (report.ai_status || report.ai_screening_status) === "failed"
                    ? "Screening indicators could not be determined."
                    : "No distinct terrain displacement signatures currently flagged."}
                </p>
              )}
            </div>

            {/* AI Summary Observation / Narrative */}
            {report.ai_summary && (
              <div
                style={{
                  padding: "10px 12px",
                  borderRadius: "4px",
                  backgroundColor: "var(--surface)",
                  border: (report.ai_status || report.ai_screening_status) === "unavailable"
                    ? "1px solid rgba(245, 158, 11, 0.3)"
                    : (report.ai_status || report.ai_screening_status) === "failed"
                    ? "1px solid rgba(239, 68, 68, 0.3)"
                    : "1px solid var(--line)",
                  marginBottom: "14px",
                }}
              >
                <span style={{ display: "block", fontSize: "10px", fontFamily: "'DM Mono'", color: "var(--text-secondary)", marginBottom: "4px" }}>
                  OBSERVATIONAL SUMMARY
                </span>
                <p
                  style={{
                    font: "400 12px/1.5 'DM Sans'",
                    color: "var(--text-primary)",
                    margin: 0,
                    whiteSpace: "pre-line",
                  }}
                >
                  {report.ai_summary.includes("503") || report.ai_summary.includes("UNAVAILABLE") || report.ai_summary.includes("high demand")
                    ? "[UNAVAILABLE] AI screening temporarily unavailable — retry later."
                    : report.ai_summary}
                </p>
              </div>
            )}

            {/* Timestamp of Screening */}
            {report.ai_analyzed_at && (
              <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontFamily: "'DM Mono'", color: "var(--text-secondary)", marginBottom: "14px" }}>
                <Clock size={12} />
                <span>Screened: {new Date(report.ai_analyzed_at).toLocaleString("en-IN")}</span>
              </div>
            )}

            {/* Trigger / Retry Button & Notifications */}
            {aiSuccess && (
              <div
                style={{
                  padding: "8px 12px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  color: "#059669",
                  fontSize: "12px",
                  fontFamily: "'DM Sans'",
                  marginBottom: "12px",
                }}
              >
                {aiSuccess}
              </div>
            )}
            {aiError && (
              <div
                style={{
                  padding: "8px 12px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(239, 68, 68, 0.1)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  color: "#dc2626",
                  fontSize: "12px",
                  fontFamily: "'DM Sans'",
                  marginBottom: "12px",
                }}
              >
                {aiError}
              </div>
            )}

            <div style={{ marginBottom: "16px" }}>
              <button
                type="button"
                onClick={() => handleTriggerAnalysis(true)}
                disabled={analyzing}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  width: "100%",
                  padding: "9px 14px",
                  borderRadius: "4px",
                  border: "1px solid var(--accent-text)",
                  backgroundColor: "var(--surface)",
                  color: "var(--accent-text)",
                  font: "600 12px 'Space Grotesk'",
                  cursor: analyzing ? "not-allowed" : "pointer",
                  opacity: analyzing ? 0.7 : 1,
                  transition: "all 0.15s ease",
                }}
              >
                <RefreshCw size={13} className={analyzing ? "animate-spin" : ""} />
                {analyzing
                  ? "Running Gemma Screening..."
                  : report.ai_analyzed_at
                  ? "Re-run AI Hazard Screening"
                  : "Trigger AI Hazard Screening"}
              </button>
            </div>

            {/* MANDATORY SAFETY DISCLAIMER */}
            <div
              style={{
                padding: "12px 14px",
                borderRadius: "6px",
                backgroundColor: "rgba(245, 158, 11, 0.08)",
                border: "1px solid rgba(245, 158, 11, 0.3)",
                display: "flex",
                gap: "10px",
                alignItems: "flex-start",
              }}
            >
              <AlertTriangle size={16} color="#d97706" style={{ flexShrink: 0, marginTop: "2px" }} />
              <p
                style={{
                  font: "400 11px/1.5 'DM Sans'",
                  color: "var(--text-secondary)",
                  margin: 0,
                }}
              >
                <strong style={{ color: "#d97706" }}>Safety Notice:</strong> AI hazard screening is intended solely as an observational triage aid. It does NOT replace on-site geotechnical engineering inspection or validate clearance for human occupancy.
              </p>
            </div>
          </div>

          {/* HUMAN REVIEW DECISION CONSOLE */}
          <div
            className="card"
            style={{
              padding: "24px",
              borderTop: "3px solid var(--text-primary)",
            }}
          >
            <h3
              style={{
                font: "700 15px 'Space Grotesk'",
                color: "var(--text-primary)",
                margin: "0 0 6px",
              }}
            >
              Human Review &amp; Adjudication Console
            </h3>
            <p
              style={{
                font: "400 13px 'DM Sans'",
                color: "var(--text-secondary)",
                margin: "0 0 16px",
              }}
            >
              Select the administrative determination for this field report. Decisions update central records and notify field dispatchers.
            </p>

            {/* Authorization Disclaimer */}
            <div
              style={{
                padding: "8px 12px",
                borderRadius: "4px",
                backgroundColor: "rgba(245, 158, 11, 0.08)",
                border: "1px solid rgba(245, 158, 11, 0.25)",
                marginBottom: "16px",
                display: "flex",
                gap: "8px",
                alignItems: "center",
              }}
            >
              <ShieldAlert size={14} color="#d97706" style={{ flexShrink: 0 }} />
              <span style={{ fontSize: "11px", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                <strong>Local Development Console:</strong> Central backend RBAC/auth middleware is pending. Review determinations update PostgreSQL records directly without individual reviewer session signatures.
              </span>
            </div>

            {/* Status Selection Buttons */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px", marginBottom: "20px" }}>
              <button
                type="button"
                onClick={() => setSelectedStatus("verified")}
                style={{
                  padding: "10px 8px",
                  borderRadius: "6px",
                  border:
                    selectedStatus === "verified"
                      ? "2px solid #059669"
                      : "1px solid var(--line)",
                  backgroundColor:
                    selectedStatus === "verified" ? "rgba(16, 185, 129, 0.12)" : "var(--surface)",
                  color: selectedStatus === "verified" ? "#059669" : "var(--text-secondary)",
                  cursor: "pointer",
                  textAlign: "center",
                  font: "700 11px 'DM Mono'",
                }}
              >
                <CheckCircle2 size={16} style={{ margin: "0 auto 4px" }} />
                VERIFY
              </button>

              <button
                type="button"
                onClick={() => setSelectedStatus("needs_inspection")}
                style={{
                  padding: "10px 8px",
                  borderRadius: "6px",
                  border:
                    selectedStatus === "needs_inspection" || selectedStatus === "under_review"
                      ? "2px solid #d97706"
                      : "1px solid var(--line)",
                  backgroundColor:
                    selectedStatus === "needs_inspection" || selectedStatus === "under_review"
                      ? "rgba(245, 158, 11, 0.12)"
                      : "var(--surface)",
                  color:
                    selectedStatus === "needs_inspection" || selectedStatus === "under_review"
                      ? "#d97706"
                      : "var(--text-secondary)",
                  cursor: "pointer",
                  textAlign: "center",
                  font: "700 11px 'DM Mono'",
                }}
              >
                <AlertTriangle size={16} style={{ margin: "0 auto 4px" }} />
                INSPECT
              </button>

              <button
                type="button"
                onClick={() => setSelectedStatus("rejected")}
                style={{
                  padding: "10px 8px",
                  borderRadius: "6px",
                  border:
                    selectedStatus === "rejected"
                      ? "2px solid #dc2626"
                      : "1px solid var(--line)",
                  backgroundColor:
                    selectedStatus === "rejected" ? "rgba(239, 68, 68, 0.12)" : "var(--surface)",
                  color: selectedStatus === "rejected" ? "#dc2626" : "var(--text-secondary)",
                  cursor: "pointer",
                  textAlign: "center",
                  font: "700 11px 'DM Mono'",
                }}
              >
                <XCircle size={16} style={{ margin: "0 auto 4px" }} />
                REJECT
              </button>
            </div>

            {/* Admin Notes */}
            <div style={{ marginBottom: "20px" }}>
              <label
                style={{
                  display: "block",
                  font: "600 12px 'DM Mono'",
                  color: "var(--text-secondary)",
                  marginBottom: "8px",
                  letterSpacing: "0.5px",
                }}
              >
                ADMINISTRATIVE REVIEW DIRECTIVE / NOTES
              </label>
              <textarea
                rows={4}
                value={adminNotes}
                onChange={(e) => setAdminNotes(e.target.value)}
                placeholder="Document verification reasoning, field team instructions, or geotechnical follow-up orders..."
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "4px",
                  border: "1px solid var(--line)",
                  backgroundColor: "var(--surface)",
                  color: "var(--text-primary)",
                  font: "400 13px/1.5 'DM Sans'",
                  outline: "none",
                  boxSizing: "border-box",
                }}
              />
            </div>

            {/* Action Buttons & Feedback */}
            {saveSuccess && (
              <div
                style={{
                  padding: "10px 12px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(16, 185, 129, 0.1)",
                  border: "1px solid rgba(16, 185, 129, 0.3)",
                  color: "#059669",
                  fontSize: "12px",
                  fontFamily: "'DM Sans', sans-serif",
                  fontWeight: 600,
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  marginBottom: "14px",
                }}
              >
                <Check size={14} /> Review decision saved and logged successfully.
              </div>
            )}

            {saveError && (
              <div
                style={{
                  padding: "10px 12px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(239, 68, 68, 0.1)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  color: "#dc2626",
                  fontSize: "12px",
                  fontFamily: "'DM Sans', sans-serif",
                  marginBottom: "14px",
                }}
              >
                {saveError}
              </div>
            )}

            <button
              type="button"
              onClick={handleSaveDecision}
              disabled={saving}
              className="btn btn-primary"
              style={{
                width: "100%",
                padding: "12px",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: "8px",
                font: "600 14px 'DM Sans'",
                cursor: saving ? "not-allowed" : "pointer",
                opacity: saving ? 0.7 : 1,
              }}
            >
              <Save size={16} />
              {saving ? "Saving Review..." : "Confirm & Save Review Decision"}
            </button>

            {/* Review Audit Info */}
            {report.reviewed_at && (
              <div
                style={{
                  marginTop: "16px",
                  paddingTop: "14px",
                  borderTop: "1px solid var(--line)",
                  font: "400 11px 'DM Mono'",
                  color: "var(--text-secondary)",
                }}
              >
                Last reviewed: {new Date(report.reviewed_at).toLocaleTimeString()},{" "}
                {new Date(report.reviewed_at).toLocaleDateString()}
                {report.reviewed_by ? ` by ${report.reviewed_by}` : ""}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
