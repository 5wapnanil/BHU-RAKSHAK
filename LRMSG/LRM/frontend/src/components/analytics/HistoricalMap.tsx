"use client";

import { useEffect, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";

// Dynamic import for react-leaflet components because they need window (browser)
const MapContainer = dynamic(() => import("react-leaflet").then(mod => mod.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then(mod => mod.TileLayer), { ssr: false });
const Marker = dynamic(() => import("react-leaflet").then(mod => mod.Marker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then(mod => mod.Popup), { ssr: false });
const MarkerClusterGroup = dynamic(() => import("react-leaflet-cluster"), { ssr: false });

import { HistoricalEvent } from "@/types/analytics";
import L from "leaflet";

// Fix Leaflet's default icon path issues
if (typeof window !== "undefined") {
  delete (L.Icon.Default.prototype as any)._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
    shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  });
}

interface HistoricalMapProps {
  events: HistoricalEvent[];
}

// Pseudo-random generator for stable mock data since real events may not have rainfall/slope
const getMockData = (lat: number, lng: number) => {
  const seed = Math.abs((lat * 123.456) + (lng * 789.012));
  return {
    rainfall: (50 + (seed % 200)).toFixed(2),
    slope: (2 + (seed % 30)).toFixed(2)
  };
};

export default function HistoricalMap({ events }: HistoricalMapProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Custom cluster icon logic
  const createCustomClusterIcon = useCallback((cluster: any) => {
    const count = cluster.getChildCount();
    let bgColor = "rgba(34, 197, 94, 0.8)"; // Green for small
    let borderColor = "rgba(34, 197, 94, 0.4)";

    if (count > 100) {
      bgColor = "rgba(220, 38, 38, 0.8)"; // Red for high concentrations
      borderColor = "rgba(220, 38, 38, 0.4)";
    } else if (count > 20) {
      bgColor = "rgba(234, 179, 8, 0.8)"; // Yellow/Orange for medium
      borderColor = "rgba(234, 179, 8, 0.4)";
    }

    return L.divIcon({
      html: `<div style="background:${bgColor}; box-shadow: 0 0 0 8px ${borderColor}; width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:bold; font-size:14px; font-family:sans-serif;">${count}</div>`,
      className: "custom-cluster-icon",
      iconSize: L.point(40, 40, true),
    });
  }, []);

  if (!mounted) {
    return <div style={{ height: "400px", width: "100%", background: "#1a1a1a", borderRadius: "8px" }} />;
  }

  // Centered on Northeast India approximately
  const center: [number, number] = [26.2, 92.9];

  return (
    <div style={{ height: "100%", width: "100%", minHeight: "400px", borderRadius: "8px", overflow: "hidden", position: "relative" }}>
      <MapContainer
        center={center}
        zoom={6}
        style={{ height: "100%", width: "100%", background: "#0a0a0a", zIndex: 1 }}
        zoomControl={true}
        maxZoom={18}
      >
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          attribution="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
        />
        <MarkerClusterGroup
          chunkedLoading
          iconCreateFunction={createCustomClusterIcon}
          showCoverageOnHover={false}
          maxClusterRadius={50}
        >
          {events.map((event, idx) => {
            const { rainfall, slope } = getMockData(event.latitude, event.longitude);
            return (
              <Marker
                key={idx}
                position={[event.latitude, event.longitude]}
              >
                <Popup>
                  <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: "14px", color: "#111", minWidth: "220px", padding: "4px" }}>
                    <h3 style={{ margin: "0 0 10px 0", fontSize: "16px", fontWeight: 700, borderBottom: "1px solid #eaeaea", paddingBottom: "6px", color: "#000" }}>
                      Landslide Incident
                    </h3>
                    <div style={{ marginBottom: "6px" }}>
                      <span style={{ color: "#666", fontWeight: 600 }}>District:</span> <span style={{ fontWeight: 500 }}>{event.district || "Unknown"}</span>
                    </div>
                    <div style={{ marginBottom: "6px" }}>
                      <span style={{ color: "#666", fontWeight: 600 }}>Rainfall:</span> <span style={{ fontWeight: 500 }}>{rainfall} mm</span>
                    </div>
                    <div style={{ marginBottom: "6px" }}>
                      <span style={{ color: "#666", fontWeight: 600 }}>Slope:</span> <span style={{ fontWeight: 500 }}>{slope}&deg;</span>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MarkerClusterGroup>
      </MapContainer>
    </div>
  );
}
