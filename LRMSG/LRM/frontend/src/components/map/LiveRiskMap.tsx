"use client";

import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useNetworkStatus } from "@/contexts/NetworkContext";
import { saveGISDataToCache, getCachedGISData } from "@/lib/db";

interface Prediction {
  name: string;
  state: string;
  lat: number;
  lng: number;
  probability: number;
  rainfall: number;
  slope: number;
}

interface BlockedRoad {
  name: string;
  coords: [number, number][];
  status: string;
}

export default function LiveRiskMap() {
  const { isOnline } = useNetworkStatus();
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const heatLayerRef = useRef<any>(null);
  const lastDataTimestampRef = useRef<any>(null);

  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [isCachedData, setIsCachedData] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      let json: any = null;
      let cachedFlag = false;
      let cacheTimestamp: number | null = null;
      
      if (isOnline) {
        try {
          const res = await fetch('/api/live-risk-predictions');
          if (res.ok) {
            json = await res.json();
            await saveGISDataToCache('live_map_data', json);
            cachedFlag = false;
            setIsCachedData(false);
          }
        } catch (err) {
          console.warn("Online fetch failed, falling back to cache");
        }
      }
      
      if (!json) {
        const cached = await getCachedGISData('live_map_data');
        if (cached && cached.data) {
          json = cached.data;
          cachedFlag = true;
          cacheTimestamp = cached.cachedAt;
          setIsCachedData(true);
        } else {
          setLoading(false);
          return; // No cache available
        }
      }
      
      const { predictions, blockedRoads } = json.data as { predictions: Prediction[], blockedRoads: BlockedRoad[] };
      const currentTimestamp = json.timestamp || cacheTimestamp;
      
      // If data hasn't changed, don't recreate layers to completely eliminate flickering
      if (lastDataTimestampRef.current === currentTimestamp) {
        setLoading(false);
        return;
      }
      lastDataTimestampRef.current = currentTimestamp;

      if (!mapInstanceRef.current) return;
      
      const heatPoints = predictions
        .filter(p => p.probability !== null && p.probability !== undefined)
        .map(p => [p.lat, p.lng, (p.probability as number) / 100]);

      // 0. HEATMAP LAYER
      if (!heatLayerRef.current && (L as any).heatLayer) {
        heatLayerRef.current = (L as any).heatLayer(heatPoints, {
          radius: 35,
          blur: 25,
          gradient: {
            0.2: '#22c55e', 
            0.5: '#eab308', 
            0.8: '#ef4444'
          }
        }).addTo(mapInstanceRef.current);
      } else if (heatLayerRef.current) {
        heatLayerRef.current.setLatLngs(heatPoints);
      }

      // 1. ZONES AND ROADS (Using Double Buffering)
      const newLayer = L.layerGroup();

      predictions.forEach(p => {
        let status = "Unavailable";
        let fill = "rgba(107, 114, 128, 0.6)"; // Gray
        let stroke = "rgba(107, 114, 128, 1)";
        
        if (p.probability !== null && p.probability !== undefined) {
          if (p.probability >= 60) {
            status = "High Risk";
            fill = "rgba(239, 68, 68, 0.7)"; // Red
            stroke = "rgba(239, 68, 68, 1)";
          } else if (p.probability >= 40) {
            status = "Medium Risk";
            fill = "rgba(234, 179, 8, 0.7)"; // Yellow
            stroke = "rgba(234, 179, 8, 1)";
          } else {
            status = "Low Risk";
            fill = "rgba(34, 197, 94, 0.6)"; // Green
            stroke = "rgba(34, 197, 94, 1)";
          }
        }

        const iconHtml = `
          <div style="
            background: ${fill};
            border: 2px solid ${stroke};
            border-radius: 50%;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-family: 'Space Grotesk', sans-serif;
            font-size: 16px;
            font-weight: 700;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            text-shadow: 0 1px 3px rgba(0,0,0,0.5);
            backdrop-filter: blur(4px);
          ">
            ${Math.round(p.probability)}%
          </div>
        `;

        const marker = L.marker([p.lat, p.lng], {
          icon: L.divIcon({
            className: 'custom-div-icon',
            html: iconHtml,
            iconSize: [48, 48],
            iconAnchor: [24, 24]
          })
        });

        const popupHtml = `
          <div style="font-family:'Space Grotesk',sans-serif; min-width:220px; padding:4px;">
            ${cachedFlag ? `<div style="background: #ef4444; color: white; padding: 4px; font-size: 10px; font-weight: bold; text-align: center; margin-bottom: 8px; border-radius: 4px;">CACHED RISK DATA (STALE)</div>` : ''}
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eaeaea; padding-bottom:6px; margin-bottom:10px;">
              <h3 style="margin:0; font-size:16px; font-weight:700;">${p.name}</h3>
              <span style="font-size:10px; font-weight:700; color:#fff; background:${stroke}; padding:2px 6px; border-radius:4px; text-transform:uppercase;">${status}</span>
            </div>
            <div style="margin-bottom:6px; font-family:'DM Sans',sans-serif; font-size:12px; color:#666;">
              State: <strong style="color:#222;">${p.state}</strong>
            </div>
            <div style="margin-bottom:6px; font-family:'DM Sans',sans-serif; font-size:12px; color:#666;">
              ${cachedFlag ? 'Cached ' : ''}ML Probability: <strong style="color:${stroke};">${p.probability.toFixed(1)}%</strong>
            </div>
            <div style="margin-bottom:6px; font-family:'DM Sans',sans-serif; font-size:12px; color:#666;">
              Local Slope: <strong style="color:#222;">${p.slope}&deg;</strong>
            </div>
            <div style="font-family:'DM Sans',sans-serif; font-size:12px; color:#666;">
              ${cachedFlag ? 'Cached ' : ''}Rainfall: <strong style="color:#222;">${p.rainfall} mm</strong>
            </div>
          </div>
        `;

        marker.bindPopup(popupHtml);
        marker.bindTooltip(
          `<div style="font-family:'DM Mono',monospace; font-size:11px; font-weight:bold;">${p.name.toUpperCase()} <br/> <span style="color:${stroke}">${p.probability.toFixed(1)}% ${cachedFlag ? 'CACHED RISK' : 'RISK'}</span></div>`, 
          { direction: 'top', opacity: 0.9, offset: [0, -10] }
        );
        marker.addTo(newLayer);
      });

      // 2. Blocked Roads
      blockedRoads.forEach(road => {
        const polyline = L.polyline(road.coords, {
          color: road.status === "Closed" ? "#ef4444" : "#eab308",
          weight: 4,
          dashArray: road.status === "Closed" ? "" : "8, 10",
          opacity: 0.9
        });

        polyline.bindTooltip(`
          <div style="font-family:'DM Mono',monospace; font-size:11px;">
            <strong>${road.name}</strong><br/>
            Status: <span style="color:${road.status === "Closed" ? "#ef4444" : "#eab308"}">${road.status.toUpperCase()}</span>
          </div>
        `, { sticky: true });
        
        polyline.addTo(newLayer);
      });

      newLayer.addTo(mapInstanceRef.current);
      if (layerGroupRef.current) {
        mapInstanceRef.current.removeLayer(layerGroupRef.current);
      }
      layerGroupRef.current = newLayer;

      if (cachedFlag && cacheTimestamp) {
        setLastUpdated(new Date(cacheTimestamp).toLocaleString());
      } else {
        setLastUpdated(new Date(json.timestamp).toLocaleTimeString());
      }
      setLoading(false);
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: [26.0, 92.5],
      zoom: 7,
      zoomControl: false,
    });

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Esri World Imagery
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS',
      maxZoom: 18
    }).addTo(map);

    const layer = L.layerGroup().addTo(map);
    layerGroupRef.current = layer;
    mapInstanceRef.current = map;

    // We must load leaflet.heat dynamically since it modifies the window.L object
    require('leaflet.heat');

    fetchData();

    const interval = setInterval(fetchData, 30000); // Polling every 30s
    return () => {
      clearInterval(interval);
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  return (
    <div style={{ position: "relative", height: "100%", width: "100%", overflow: "hidden", borderRadius: "16px" }}>
      <div ref={mapRef} style={{ height: "100%", width: "100%", background: "#000" }} />
      
      {/* Sleek UI Overlay */}
      <div style={{
        position: "absolute",
        top: "24px",
        left: "24px",
        zIndex: 1000,
        background: "rgba(255, 255, 255, 0.95)",
        backdropFilter: "blur(12px)",
        border: "1px solid rgba(0,0,0,0.1)",
        borderRadius: "12px",
        padding: "20px",
        color: "#111",
        boxShadow: "0 20px 40px rgba(0,0,0,0.15)",
        minWidth: "240px"
      }}>
        <h3 style={{ margin: "0 0 16px 0", fontSize: "14px", fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "1px", color: "#222", display: "flex", alignItems: "center", gap: "8px", fontWeight: 700 }}>
          <span style={{ fontSize: "16px" }}>🛰️</span> ML RISK ENGINE
        </h3>
        
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "20px", fontSize: "11px", fontFamily: "'DM Mono', monospace", fontWeight: 600 }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: isCachedData ? "#ef4444" : (loading ? "#eab308" : "#22c55e"), boxShadow: isCachedData ? "0 0 8px #ef4444" : (loading ? "0 0 8px #eab308" : "0 0 8px #22c55e") }} />
          <span style={{ color: isCachedData ? "#ef4444" : (loading ? "#eab308" : "#22c55e") }}>
            {isCachedData ? "OFFLINE — CACHED RISK DATA" : (loading ? "SYNCING..." : "LIVE FEED")}
          </span>
          <span style={{ marginLeft: "auto", color: "#666" }}>{lastUpdated}</span>
        </div>

        <div style={{ borderTop: "1px solid rgba(0,0,0,0.1)", paddingTop: "16px", fontSize: "12px", fontFamily: "'DM Sans', sans-serif", fontWeight: 500 }}>
          <div style={{ marginBottom: "12px", fontWeight: 700, fontSize: "10px", color: "#666", letterSpacing: "1px" }}>ZONE RISK LEVEL</div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <div style={{ width: "14px", height: "14px", background: "rgba(239, 68, 68, 0.8)", border: "2px solid #ef4444", borderRadius: "50%" }} />
            <span>High Risk (&ge; 60%)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <div style={{ width: "14px", height: "14px", background: "rgba(234, 179, 8, 0.8)", border: "2px solid #eab308", borderRadius: "50%" }} />
            <span>Medium Risk (&ge; 40%)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px" }}>
            <div style={{ width: "14px", height: "14px", background: "rgba(34, 197, 94, 0.8)", border: "2px solid #22c55e", borderRadius: "50%" }} />
            <span>Safe (&lt; 40%)</span>
          </div>

          <div style={{ marginBottom: "12px", fontWeight: 700, fontSize: "10px", color: "#666", letterSpacing: "1px" }}>INFRASTRUCTURE</div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <div style={{ width: "20px", height: "4px", background: "#ef4444" }} />
            <span>Closed Highway</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{ width: "20px", height: "4px", background: "#eab308", borderBottom: "1px dashed #000" }} />
            <span>Partial Blockade</span>
          </div>
        </div>
      </div>
    </div>
  );
}
