"use client";

import { useEffect, useState, useMemo } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { FieldReport, ReviewStatus } from "@/types/fieldReport";
import { fetchFieldReports } from "@/lib/fieldReports";
import {
  MapPin,
  Filter,
  RefreshCw,
  ArrowRight,
  ExternalLink,
  Layers,
  AlertCircle,
  PlusCircle,
  Clock,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ChevronRight,
} from "lucide-react";

// Dynamic import with ssr: false for client-only Leaflet rendering
const DashboardReportsMap = dynamic(
  () => import("@/components/dashboard/DashboardReportsMap"),
  {
    ssr: false,
    loading: () => (
      <div
        style={{
          width: "100%",
          height: "560px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "var(--paper)",
          border: "1px solid var(--line)",
          borderRadius: "8px",
          color: "var(--text-secondary)",
          gap: "10px",
          font: "500 14px 'DM Sans'",
        }}
      >
        <RefreshCw size={24} className="animate-spin" />
        Initializing GIS Map View...
      </div>
    ),
  }
);

export default function DashboardMapPage() {
  const [reports, setReports] = useState<FieldReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>("all");
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFieldReports();
      setReports(data);
    } catch (err: any) {
      setError("Unable to retrieve field reports for mapping. Verify FastAPI is online.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const geotaggedReports = useMemo(() => {
    return reports.filter(
      (r) =>
        typeof r.latitude === "number" &&
        !isNaN(r.latitude) &&
        typeof r.longitude === "number" &&
        !isNaN(r.longitude)
    );
  }, [reports]);

  const filteredReports = useMemo(() => {
    if (selectedFilter === "all") return geotaggedReports;
    return geotaggedReports.filter((r) => r.review_status === selectedFilter);
  }, [geotaggedReports, selectedFilter]);

  const selectedReport = useMemo(() => {
    if (!selectedReportId) return null;
    return reports.find((r) => r.id === selectedReportId) || null;
  }, [reports, selectedReportId]);

  return (
    <div style={{ maxWidth: "1400px", paddingBottom: "40px" }}>
      {/* Top Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: "16px",
          marginBottom: "24px",
          borderBottom: "1px solid var(--line)",
          paddingBottom: "20px",
        }}
      >
        <div>
          <p className="eyebrow" style={{ marginBottom: "6px" }}>
            SPATIAL HAZARD DISTRIBUTION
          </p>
          <h1
            style={{
              font: "700 clamp(24px, 4vw, 32px) 'Space Grotesk'",
              letterSpacing: "-0.5px",
              color: "var(--text-primary)",
              margin: 0,
            }}
          >
            Geographic Field Map
          </h1>
          <p
            style={{
              font: "400 14px/1.5 'DM Sans'",
              color: "var(--text-secondary)",
              margin: "6px 0 0",
            }}
          >
            Geotagged ground observations across vulnerable mountain slopes and transportation corridors.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button
            onClick={loadData}
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
            + Submit Geotagged Report
          </Link>
        </div>
      </div>

      {/* Filter and Stats Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          marginBottom: "16px",
        }}
      >
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
          {[
            { label: "All Geotagged", value: "all" },
            { label: "Awaiting Review", value: "pending" },
            { label: "Under Review", value: "under_review" },
            { label: "Verified", value: "verified" },
            { label: "Rejected", value: "rejected" },
          ].map((tab) => {
            const isSelected = selectedFilter === tab.value;
            const count =
              tab.value === "all"
                ? geotaggedReports.length
                : geotaggedReports.filter((r) => r.review_status === tab.value).length;

            return (
              <button
                key={tab.value}
                onClick={() => setSelectedFilter(tab.value)}
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

        <div
          style={{
            font: "600 12px 'DM Mono'",
            color: "var(--text-secondary)",
            letterSpacing: "0.5px",
          }}
        >
          {geotaggedReports.length} OF {reports.length} REPORTS GEOTAGGED
        </div>
      </div>

      {/* Map Layout: Left (Leaflet Map) / Right (Interactive Feed / Selection) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 340px",
          gap: "20px",
          minHeight: "580px",
        }}
        className="map-view-grid"
      >
        {/* MAP CONTAINER */}
        <div
          className="card"
          style={{
            padding: 0,
            overflow: "hidden",
            height: "600px",
            border: "1px solid var(--line)",
            position: "relative",
          }}
        >
          {loading ? (
            <div
              style={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--text-secondary)",
                font: "500 14px 'DM Sans'",
              }}
            >
              <RefreshCw size={24} className="animate-spin" style={{ marginBottom: "10px" }} />
              Loading geotagged observations...
            </div>
          ) : filteredReports.length === 0 ? (
            <div
              style={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "24px",
                textAlign: "center",
              }}
            >
              <MapPin size={36} color="var(--text-secondary)" style={{ marginBottom: "12px", opacity: 0.5 }} />
              <h3 style={{ font: "700 16px 'Space Grotesk'", color: "var(--text-primary)", margin: "0 0 6px" }}>
                No geotagged reports in this view
              </h3>
              <p style={{ font: "400 13px 'DM Sans'", color: "var(--text-secondary)", maxWidth: "340px", margin: "0 0 16px" }}>
                Reports submitted with GPS coordinates or location tags appear on this interactive map.
              </p>
              <Link
                href="/report"
                className="btn btn-primary"
                style={{ padding: "8px 16px", font: "600 12px 'DM Sans'" }}
              >
                Submit Geotagged Report
              </Link>
            </div>
          ) : (
            <DashboardReportsMap
              reports={filteredReports}
              selectedReportId={selectedReportId}
              onSelectReport={(r) => setSelectedReportId(r.id)}
            />
          )}
        </div>

        {/* SIDEBAR: REPORT LIST & SELECTION */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "12px",
            height: "600px",
          }}
        >
          <div
            className="card"
            style={{
              padding: "16px",
              flex: "1",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "12px",
                borderBottom: "1px solid var(--line)",
                paddingBottom: "10px",
              }}
            >
              <span style={{ font: "700 12px 'DM Mono'", color: "var(--text-secondary)", letterSpacing: "0.5px" }}>
                GEOTAGGED FEED ({filteredReports.length})
              </span>
              {selectedReportId && (
                <button
                  onClick={() => setSelectedReportId(null)}
                  style={{
                    border: "none",
                    background: "none",
                    color: "var(--accent-text)",
                    fontSize: "11px",
                    fontFamily: "'DM Sans'",
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  Clear Selection
                </button>
              )}
            </div>

            <div
              style={{
                flex: "1",
                overflowY: "auto",
                display: "flex",
                flexDirection: "column",
                gap: "8px",
                paddingRight: "4px",
              }}
            >
              {filteredReports.map((report) => {
                const isSelected = report.id === selectedReportId;
                return (
                  <div
                    key={report.id}
                    onClick={() => setSelectedReportId(report.id)}
                    style={{
                      padding: "12px",
                      borderRadius: "6px",
                      border: isSelected
                        ? "1.5px solid var(--accent-text)"
                        : "1px solid var(--line)",
                      backgroundColor: isSelected ? "var(--paper)" : "var(--surface)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                      <span
                        style={{
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "11px",
                          fontWeight: 700,
                          color: "var(--accent-text)",
                        }}
                      >
                        #{report.id.slice(0, 8)}
                      </span>
                      <span
                        style={{
                          fontFamily: "'DM Mono', monospace",
                          fontSize: "10px",
                          fontWeight: 700,
                          color:
                            report.review_status === "verified"
                              ? "#059669"
                              : report.review_status === "under_review"
                              ? "#d97706"
                              : report.review_status === "rejected"
                              ? "#dc2626"
                              : "var(--text-secondary)",
                        }}
                      >
                        {report.review_status.toUpperCase()}
                      </span>
                    </div>

                    <div
                      style={{
                        fontFamily: "'Space Grotesk', sans-serif",
                        fontSize: "13px",
                        fontWeight: 600,
                        color: "var(--text-primary)",
                        marginBottom: "4px",
                      }}
                    >
                      {report.location_name}
                    </div>

                    <div
                      style={{
                        fontSize: "11px",
                        color: "var(--text-secondary)",
                        fontFamily: "'DM Sans'",
                        lineHeight: "1.4",
                        maxHeight: "32px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        marginBottom: "8px",
                      }}
                    >
                      {report.notes}
                    </div>

                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontSize: "10px",
                        fontFamily: "'DM Mono', monospace",
                        color: "var(--text-secondary)",
                      }}
                    >
                      <span>
                        {report.latitude?.toFixed(3)}, {report.longitude?.toFixed(3)}
                      </span>
                      <Link
                        href={`/dashboard/reports/${report.id}`}
                        onClick={(e) => e.stopPropagation()}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "3px",
                          color: "var(--accent-text)",
                          fontWeight: 700,
                          textDecoration: "none",
                        }}
                      >
                        Inspect &rarr;
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
