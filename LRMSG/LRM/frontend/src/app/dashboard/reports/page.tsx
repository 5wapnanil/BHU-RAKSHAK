"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { FieldReport, ReviewStatus } from "@/types/fieldReport";
import { fetchFieldReports } from "@/lib/fieldReports";
import {
  ClipboardList,
  Search,
  Filter,
  MapPin,
  Clock,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
  PlusCircle,
  RefreshCw,
  ExternalLink,
  Cpu,
  Image as ImageIcon,
} from "lucide-react";

const STATUS_FILTERS: { label: string; value: string; countKey?: ReviewStatus }[] = [
  { label: "All Reports", value: "all" },
  { label: "Awaiting Review", value: "pending", countKey: "pending" },
  { label: "Needs Inspection", value: "needs_inspection", countKey: "needs_inspection" },
  { label: "Verified", value: "verified", countKey: "verified" },
  { label: "Rejected", value: "rejected", countKey: "rejected" },
];

export default function FieldReportsListPage() {
  const [reports, setReports] = useState<FieldReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");

  async function loadReports() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFieldReports();
      setReports(data);
    } catch (err: any) {
      setError("Unable to load field reports from backend. Please verify FastAPI is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, []);

  const counts = useMemo(() => {
    const c: Record<string, number> = {
      all: reports.length,
      pending: 0,
      needs_inspection: 0,
      under_review: 0,
      verified: 0,
      rejected: 0,
    };
    for (const r of reports) {
      if (c[r.review_status] !== undefined) {
        c[r.review_status]++;
      }
      if (r.review_status === "needs_inspection") {
        c.under_review++;
      }
    }
    return c;
  }, [reports]);

  const filteredReports = useMemo(() => {
    return reports.filter((r) => {
      // Filter by status tab
      if (activeFilter !== "all" && r.review_status !== activeFilter) {
        return false;
      }
      // Filter by search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchId = r.id.toLowerCase().includes(q);
        const matchLoc = r.location_name.toLowerCase().includes(q);
        const matchNotes = r.notes.toLowerCase().includes(q);
        const matchReporter = (r.reporter_name || "").toLowerCase().includes(q);
        return matchId || matchLoc || matchNotes || matchReporter;
      }
      return true;
    });
  }, [reports, activeFilter, searchQuery]);

  function renderStatusBadge(status: ReviewStatus) {
    switch (status) {
      case "verified":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "3px 8px",
              borderRadius: "4px",
              fontSize: "11px",
              fontFamily: "'DM Mono', monospace",
              fontWeight: 700,
              backgroundColor: "rgba(16, 185, 129, 0.12)",
              color: "#059669",
              border: "1px solid rgba(16, 185, 129, 0.3)",
            }}
          >
            <CheckCircle2 size={12} />
            VERIFIED
          </span>
        );
      case "needs_inspection":
      case "under_review":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "3px 8px",
              borderRadius: "4px",
              fontSize: "11px",
              fontFamily: "'DM Mono', monospace",
              fontWeight: 700,
              backgroundColor: "rgba(245, 158, 11, 0.12)",
              color: "#d97706",
              border: "1px solid rgba(245, 158, 11, 0.3)",
            }}
          >
            <AlertTriangle size={12} />
            NEEDS INSPECTION
          </span>
        );
      case "rejected":
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "3px 8px",
              borderRadius: "4px",
              fontSize: "11px",
              fontFamily: "'DM Mono', monospace",
              fontWeight: 700,
              backgroundColor: "rgba(239, 68, 68, 0.12)",
              color: "#dc2626",
              border: "1px solid rgba(239, 68, 68, 0.3)",
            }}
          >
            <XCircle size={12} />
            REJECTED
          </span>
        );
      default:
        return (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "3px 8px",
              borderRadius: "4px",
              fontSize: "11px",
              fontFamily: "'DM Mono', monospace",
              fontWeight: 700,
              backgroundColor: "rgba(100, 116, 139, 0.12)",
              color: "var(--text-secondary)",
              border: "1px solid var(--line)",
            }}
          >
            <HelpCircle size={12} />
            AWAITING REVIEW
          </span>
        );
    }
  }

  function renderAIBadge(report: FieldReport) {
    const status = report.ai_status || report.ai_screening_status;
    if (status === "completed" && report.ai_hazard_level) {
      const isCritical = report.ai_hazard_level === "critical";
      const isHigh = report.ai_hazard_level === "high";
      const isMod = report.ai_hazard_level === "moderate";
      const color = isCritical ? "#ef4444" : isHigh ? "#f97316" : isMod ? "#f59e0b" : "var(--accent-text)";
      return (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "11px",
            fontFamily: "'DM Mono', monospace",
            fontWeight: 700,
            color,
          }}
          title={`AI Hazard Level: ${report.ai_hazard_level} (${typeof report.ai_confidence === "number" ? Math.round(report.ai_confidence * 100) + '% (uncalibrated)' : 'unavailable'})`}
        >
          <Cpu size={12} />
          {report.ai_hazard_level.toUpperCase()}
        </span>
      );
    }
    if (status === "processing") {
      return (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "11px",
            fontFamily: "'DM Mono', monospace",
            color: "#3b82f6",
          }}
        >
          <RefreshCw size={11} className="animate-spin" />
          ANALYZING...
        </span>
      );
    }
    if (status === "failed") {
      return (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "11px",
            fontFamily: "'DM Mono', monospace",
            color: "#ef4444",
          }}
          title="AI screening failed"
        >
          <AlertTriangle size={12} />
          AI FAILED
        </span>
      );
    }
    if (status === "unavailable") {
      const isTemp =
        report.ai_summary?.toLowerCase().includes("temporarily unavailable") ||
        report.ai_summary?.includes("503") ||
        report.ai_summary?.includes("UNAVAILABLE") ||
        report.ai_summary?.toLowerCase().includes("retry");
      return (
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "11px",
            fontFamily: "'DM Mono', monospace",
            color: isTemp ? "#f59e0b" : "var(--text-secondary)",
          }}
          title={isTemp ? "AI screening temporarily unavailable — retry later" : "AI provider not configured"}
        >
          <Cpu size={12} style={{ opacity: isTemp ? 0.9 : 0.6 }} />
          {isTemp ? "AI UNAVAILABLE" : "AI OFF"}
        </span>
      );
    }
    return (
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "4px",
          fontSize: "11px",
          fontFamily: "'DM Mono', monospace",
          color: "var(--text-secondary)",
        }}
        title="AI hazard screening pending"
      >
        <Cpu size={12} style={{ opacity: 0.6 }} />
        Pending AI
      </span>
    );
  }

  return (
    <div style={{ maxWidth: "1280px" }}>
      {/* Top Header */}
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
          <p className="eyebrow" style={{ marginBottom: "6px" }}>
            INCIDENT &amp; HAZARD VERIFICATION
          </p>
          <h1
            style={{
              font: "700 clamp(24px, 4vw, 32px) 'Space Grotesk'",
              letterSpacing: "-0.5px",
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            Field Reports Registry
          </h1>
          <p
            style={{
              font: "400 14px/1.5 'DM Sans'",
              color: "var(--text-secondary)",
              margin: "6px 0 0",
              maxWidth: "600px",
            }}
          >
            Review and adjudicate ground observations submitted by local scouts and community monitors.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button
            onClick={loadReports}
            className="chip"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              cursor: "pointer",
              padding: "8px 12px",
              borderRadius: "4px",
              border: "1px solid var(--line)",
              background: "var(--surface)",
              font: "600 12px 'DM Mono'",
            }}
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            REFRESH
          </button>
          <Link
            href="/report"
            className="btn btn-primary"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "8px 16px",
              font: "600 13px 'DM Sans'",
              borderRadius: "4px",
            }}
          >
            <PlusCircle size={15} />
            + New Field Report
          </Link>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "16px",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        {/* Filter Tabs */}
        <div
          style={{
            display: "flex",
            gap: "6px",
            overflowX: "auto",
            paddingBottom: "4px",
          }}
        >
          {STATUS_FILTERS.map((tab) => {
            const count = counts[tab.value] || 0;
            const isSelected = activeFilter === tab.value;
            return (
              <button
                key={tab.value}
                onClick={() => setActiveFilter(tab.value)}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "4px",
                  border: isSelected ? "1px solid var(--accent-text)" : "1px solid var(--line)",
                  backgroundColor: isSelected ? "var(--paper)" : "transparent",
                  color: isSelected ? "var(--accent-text)" : "var(--text-secondary)",
                  font: "600 12px 'DM Sans'",
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                }}
              >
                <span>{tab.label}</span>
                <span
                  style={{
                    fontSize: "10px",
                    fontFamily: "'DM Mono', monospace",
                    padding: "1px 5px",
                    borderRadius: "10px",
                    backgroundColor: isSelected ? "var(--accent-text)" : "var(--line)",
                    color: isSelected ? "#fff" : "var(--text-secondary)",
                  }}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search input */}
        <div style={{ position: "relative", minWidth: "260px", flex: "1", maxWidth: "380px" }}>
          <Search
            size={15}
            style={{
              position: "absolute",
              left: "12px",
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--text-secondary)",
            }}
          />
          <input
            type="text"
            placeholder="Search landmark, notes, ID, reporter..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: "100%",
              padding: "8px 12px 8px 36px",
              borderRadius: "4px",
              border: "1px solid var(--line)",
              backgroundColor: "var(--surface)",
              color: "var(--text-primary)",
              font: "400 13px 'DM Sans'",
              outline: "none",
            }}
          />
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div
          className="card"
          style={{
            padding: "48px 24px",
            textAlign: "center",
            color: "var(--text-secondary)",
            font: "500 14px 'DM Sans'",
          }}
        >
          <RefreshCw size={24} className="animate-spin" style={{ margin: "0 auto 12px" }} />
          Loading field reports from database...
        </div>
      ) : error ? (
        <div
          className="card"
          style={{
            padding: "24px",
            borderLeft: "4px solid #ef4444",
            backgroundColor: "rgba(239, 68, 68, 0.05)",
          }}
        >
          <div style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
            <AlertTriangle size={20} color="#dc2626" />
            <div>
              <h4 style={{ margin: "0 0 4px", color: "#dc2626", font: "600 15px 'Space Grotesk'" }}>
                Backend Connectivity Issue
              </h4>
              <p style={{ margin: 0, font: "400 13px 'DM Sans'", color: "var(--text-secondary)" }}>
                {error}
              </p>
            </div>
          </div>
        </div>
      ) : filteredReports.length === 0 ? (
        <div
          className="card"
          style={{
            padding: "60px 24px",
            textAlign: "center",
            border: "1px dashed var(--line)",
          }}
        >
          <ClipboardList
            size={40}
            style={{ color: "var(--text-secondary)", margin: "0 auto 16px", opacity: 0.5 }}
          />
          <h3
            style={{
              font: "700 18px 'Space Grotesk'",
              color: "var(--text-primary)",
              margin: "0 0 8px",
            }}
          >
            No field reports found
          </h3>
          <p
            style={{
              font: "400 14px 'DM Sans'",
              color: "var(--text-secondary)",
              maxWidth: "460px",
              margin: "0 auto 20px",
            }}
          >
            {searchQuery
              ? `No reports matched your query "${searchQuery}". Try clearing filters or searching for another term.`
              : "No field reports currently match this filter. As field scouts submit hazard observations and the Phase 2 backend model is connected, reports will appear here for administrative review."}
          </p>
          <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="btn"
                style={{
                  border: "1px solid var(--line)",
                  padding: "8px 16px",
                  font: "600 13px 'DM Sans'",
                }}
              >
                Clear Search
              </button>
            )}
            <Link
              href="/report"
              className="btn btn-primary"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 16px",
                font: "600 13px 'DM Sans'",
              }}
            >
              <PlusCircle size={15} />
              Submit First Report
            </Link>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                textAlign: "left",
              }}
            >
              <thead>
                <tr
                  style={{
                    backgroundColor: "var(--paper)",
                    borderBottom: "1px solid var(--line)",
                  }}
                >
                  <th
                    style={{
                      padding: "12px 16px",
                      font: "700 11px 'DM Mono'",
                      color: "var(--text-secondary)",
                      letterSpacing: "0.5px",
                    }}
                  >
                    REPORT ID
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      font: "700 11px 'DM Mono'",
                      color: "var(--text-secondary)",
                      letterSpacing: "0.5px",
                    }}
                  >
                    LANDMARK &amp; SECTOR
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      font: "700 11px 'DM Mono'",
                      color: "var(--text-secondary)",
                      letterSpacing: "0.5px",
                    }}
                  >
                    OBSERVATION NOTES
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      font: "700 11px 'DM Mono'",
                      color: "var(--text-secondary)",
                      letterSpacing: "0.5px",
                    }}
                  >
                    EVIDENCE
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      font: "700 11px 'DM Mono'",
                      color: "var(--text-secondary)",
                      letterSpacing: "0.5px",
                    }}
                  >
                    SUBMITTED
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      font: "700 11px 'DM Mono'",
                      color: "var(--text-secondary)",
                      letterSpacing: "0.5px",
                    }}
                  >
                    AI SCREENING
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      font: "700 11px 'DM Mono'",
                      color: "var(--text-secondary)",
                      letterSpacing: "0.5px",
                    }}
                  >
                    STATUS
                  </th>
                  <th
                    style={{
                      padding: "12px 16px",
                      font: "700 11px 'DM Mono'",
                      color: "var(--text-secondary)",
                      letterSpacing: "0.5px",
                      textAlign: "right",
                    }}
                  >
                    ACTION
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((report) => {
                  const dateStr = new Date(report.submitted_at).toLocaleDateString("en-IN", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  });

                  return (
                    <tr
                      key={report.id}
                      style={{
                        borderBottom: "1px solid var(--line)",
                        transition: "background-color 0.1s ease",
                      }}
                      className="hover:bg-[var(--paper)]"
                    >
                      {/* ID */}
                      <td style={{ padding: "14px 16px", verticalAlign: "top" }}>
                        <span
                          style={{
                            fontFamily: "'DM Mono', monospace",
                            fontSize: "12px",
                            fontWeight: 700,
                            color: "var(--accent-text)",
                          }}
                        >
                          #{report.id.slice(0, 8)}
                        </span>
                        {report.client_op_id && (
                          <div
                            style={{
                              fontSize: "10px",
                              fontFamily: "'DM Mono', monospace",
                              color: "var(--text-secondary)",
                              marginTop: "2px",
                            }}
                          >
                            {report.client_op_id.slice(0, 14)}...
                          </div>
                        )}
                      </td>

                      {/* Landmark & Geolocation */}
                      <td style={{ padding: "14px 16px", verticalAlign: "top" }}>
                        <div
                          style={{
                            fontFamily: "'Space Grotesk', sans-serif",
                            fontSize: "13px",
                            fontWeight: 600,
                            color: "var(--text-primary)",
                          }}
                        >
                          {report.location_name}
                        </div>
                        {typeof report.latitude === "number" && typeof report.longitude === "number" ? (
                          <div
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              fontSize: "11px",
                              fontFamily: "'DM Mono', monospace",
                              color: "var(--text-secondary)",
                              marginTop: "3px",
                            }}
                          >
                            <MapPin size={11} color="var(--accent-text)" />
                            {report.latitude.toFixed(3)}, {report.longitude.toFixed(3)}
                          </div>
                        ) : (
                          <div
                            style={{
                              fontSize: "11px",
                              fontFamily: "'DM Mono', monospace",
                              color: "var(--text-secondary)",
                              marginTop: "3px",
                              opacity: 0.6,
                            }}
                          >
                            No GPS coordinates
                          </div>
                        )}
                      </td>

                      {/* Observation Notes */}
                      <td
                        style={{
                          padding: "14px 16px",
                          verticalAlign: "top",
                          maxWidth: "320px",
                        }}
                      >
                        <p
                          style={{
                            fontFamily: "'DM Sans', sans-serif",
                            fontSize: "13px",
                            color: "var(--text-primary)",
                            margin: 0,
                            overflow: "hidden",
                            display: "-webkit-box",
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: "vertical",
                          }}
                        >
                          {report.notes}
                        </p>
                        <div
                          style={{
                            fontSize: "11px",
                            fontFamily: "'DM Sans', sans-serif",
                            color: "var(--text-secondary)",
                            marginTop: "3px",
                          }}
                        >
                          Reported by: <span style={{ fontWeight: 600 }}>{report.reporter_name}</span>
                        </div>
                      </td>

                      {/* Photo Evidence */}
                      <td style={{ padding: "14px 16px", verticalAlign: "top" }}>
                        {report.photo_url ? (
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <a
                              href={report.photo_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ display: "block", textDecoration: "none" }}
                              title="Click to view full photograph"
                            >
                              <img
                                src={report.photo_url}
                                alt="Observation evidence"
                                style={{
                                  width: "48px",
                                  height: "48px",
                                  objectFit: "cover",
                                  borderRadius: "4px",
                                  border: "1px solid var(--line)",
                                  backgroundColor: "#000",
                                }}
                              />
                            </a>
                            <div style={{ display: "flex", flexDirection: "column" }}>
                              <span
                                style={{
                                  fontSize: "11px",
                                  fontFamily: "'DM Mono', monospace",
                                  fontWeight: 600,
                                  color: "var(--accent-text)",
                                }}
                              >
                                Attached
                              </span>
                              <a
                                href={report.photo_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                  fontSize: "10px",
                                  fontFamily: "'DM Sans', sans-serif",
                                  color: "var(--text-secondary)",
                                  textDecoration: "underline",
                                }}
                              >
                                View full
                              </a>
                            </div>
                          </div>
                        ) : (
                          <span
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              fontSize: "11px",
                              fontFamily: "'DM Mono', monospace",
                              color: "var(--text-secondary)",
                              opacity: 0.6,
                            }}
                          >
                            <ImageIcon size={12} />
                            No photo
                          </span>
                        )}
                      </td>

                      {/* Submitted Date */}
                      <td
                        style={{
                          padding: "14px 16px",
                          verticalAlign: "top",
                          whiteSpace: "nowrap",
                        }}
                      >
                        <div
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "5px",
                            fontSize: "12px",
                            fontFamily: "'DM Mono', monospace",
                            color: "var(--text-secondary)",
                          }}
                        >
                          <Clock size={12} />
                          {dateStr}
                        </div>
                      </td>

                      {/* AI Screening */}
                      <td style={{ padding: "14px 16px", verticalAlign: "top" }}>
                        {renderAIBadge(report)}
                      </td>

                      {/* Review Status */}
                      <td style={{ padding: "14px 16px", verticalAlign: "top" }}>
                        {renderStatusBadge(report.review_status)}
                      </td>

                      {/* Action */}
                      <td
                        style={{
                          padding: "14px 16px",
                          verticalAlign: "top",
                          textAlign: "right",
                          whiteSpace: "nowrap",
                        }}
                      >
                        <Link
                          href={`/dashboard/reports/${report.id}`}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                            padding: "5px 10px",
                            borderRadius: "4px",
                            fontSize: "12px",
                            fontFamily: "'DM Sans', sans-serif",
                            fontWeight: 600,
                            color: "var(--accent-text)",
                            border: "1px solid var(--line)",
                            backgroundColor: "var(--surface)",
                            textDecoration: "none",
                            transition: "background-color 0.15s ease",
                          }}
                          className="hover:border-[var(--accent-text)]"
                        >
                          Inspect Report
                          <ArrowRight size={13} />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
