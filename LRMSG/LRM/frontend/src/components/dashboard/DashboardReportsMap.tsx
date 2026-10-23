"use client";

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { FieldReport, ReviewStatus } from "@/types/fieldReport";
import Link from "next/link";

interface DashboardReportsMapProps {
  reports: FieldReport[];
  selectedReportId?: string | null;
  onSelectReport?: (report: FieldReport) => void;
}

const STATUS_COLOR_MAP: Record<ReviewStatus, { stroke: string; fill: string; label: string }> = {
  verified: { stroke: "#059669", fill: "rgba(16, 185, 129, 0.85)", label: "VERIFIED" },
  under_review: { stroke: "#d97706", fill: "rgba(245, 158, 11, 0.85)", label: "UNDER REVIEW" },
  rejected: { stroke: "#dc2626", fill: "rgba(239, 68, 68, 0.85)", label: "REJECTED" },
  needs_inspection: { stroke: "#7c3aed", fill: "rgba(124, 58, 237, 0.85)", label: "INSPECTION" },
  pending: { stroke: "#475569", fill: "rgba(100, 116, 139, 0.85)", label: "AWAITING REVIEW" },
};

export default function DashboardReportsMap({
  reports,
  selectedReportId,
  onSelectReport,
}: DashboardReportsMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markerLayerRef = useRef<L.LayerGroup | null>(null);
  const markerMapRef = useRef<Record<string, L.Marker>>({});

  // 1. Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Default center on Northeast India / Himalayan foothills
    const map = L.map(mapContainerRef.current, {
      center: [26.2, 92.0],
      zoom: 7,
      zoomControl: false,
    });

    L.control.zoom({ position: "bottomright" }).addTo(map);

    // OpenStreetMap standard or CartoDB Positron for clean contrast
    L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 19,
    }).addTo(map);

    const markerLayer = L.layerGroup().addTo(map);
    markerLayerRef.current = markerLayer;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
      markerLayerRef.current = null;
    };
  }, []);

  // 2. Render Markers whenever reports list changes
  useEffect(() => {
    if (!mapInstanceRef.current || !markerLayerRef.current) return;

    markerLayerRef.current.clearLayers();
    markerMapRef.current = {};

    const validReports = reports.filter(
      (r) =>
        typeof r.latitude === "number" &&
        !isNaN(r.latitude) &&
        typeof r.longitude === "number" &&
        !isNaN(r.longitude)
    );

    const bounds: [number, number][] = [];

    validReports.forEach((r) => {
      const lat = r.latitude!;
      const lng = r.longitude!;
      bounds.push([lat, lng]);

      const colors = STATUS_COLOR_MAP[r.review_status] || STATUS_COLOR_MAP.pending;

      // Custom pulse HTML icon
      const customIcon = L.divIcon({
        className: "custom-field-report-pin",
        html: `
          <div style="
            position: relative;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
          ">
            <span style="
              position: absolute;
              width: 100%;
              height: 100%;
              border-radius: 50%;
              background: ${colors.fill};
              opacity: 0.35;
              transform: scale(1.4);
            "></span>
            <span style="
              width: 18px;
              height: 18px;
              border-radius: 50%;
              background: ${colors.fill};
              border: 2px solid #ffffff;
              box-shadow: 0 2px 6px rgba(0,0,0,0.3);
              display: block;
            "></span>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const marker = L.marker([lat, lng], { icon: customIcon });

      const popupContent = `
        <div style="font-family: 'DM Sans', sans-serif; padding: 4px; min-width: 220px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-family: 'DM Mono', monospace; font-size: 11px; font-weight: 700; color: #e05a3a;">
              #${r.id.slice(0, 8)}
            </span>
            <span style="
              font-family: 'DM Mono', monospace;
              font-size: 10px;
              font-weight: 700;
              padding: 2px 6px;
              border-radius: 3px;
              background-color: ${colors.fill};
              color: #ffffff;
            ">
              ${colors.label}
            </span>
          </div>
          <div style="font-family: 'Space Grotesk', sans-serif; font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 4px;">
            ${r.location_name}
          </div>
          <div style="font-size: 12px; color: #64748b; line-height: 1.4; margin-bottom: 8px; max-height: 60px; overflow: hidden; text-overflow: ellipsis;">
            ${r.notes}
          </div>
          <div style="font-family: 'DM Mono', monospace; font-size: 10px; color: #94a3b8; margin-bottom: 8px;">
            GPS: ${lat.toFixed(4)}, ${lng.toFixed(4)}
          </div>
          <a
            href="/dashboard/reports/${r.id}"
            style="
              display: block;
              text-align: center;
              padding: 6px 10px;
              background-color: #e05a3a;
              color: #ffffff;
              text-decoration: none;
              font-size: 11px;
              font-weight: 600;
              border-radius: 4px;
            "
          >
            Inspect Report &rarr;
          </a>
        </div>
      `;

      marker.bindPopup(popupContent, { minWidth: 220 });

      marker.on("click", () => {
        if (onSelectReport) {
          onSelectReport(r);
        }
      });

      marker.addTo(markerLayerRef.current!);
      markerMapRef.current[r.id] = marker;
    });

    // Auto-fit to marker bounds if any markers exist
    if (bounds.length > 0 && mapInstanceRef.current) {
      mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
    }
  }, [reports, onSelectReport]);

  // 3. Highlight/pan to selected report if selectedReportId changes
  useEffect(() => {
    if (!selectedReportId || !mapInstanceRef.current) return;
    const marker = markerMapRef.current[selectedReportId];
    if (marker) {
      const latLng = marker.getLatLng();
      mapInstanceRef.current.flyTo(latLng, 12, { duration: 1 });
      marker.openPopup();
    }
  }, [selectedReportId]);

  return (
    <div
      ref={mapContainerRef}
      style={{
        width: "100%",
        height: "100%",
        minHeight: "540px",
        borderRadius: "8px",
        overflow: "hidden",
        position: "relative",
        zIndex: 1,
      }}
    />
  );
}
