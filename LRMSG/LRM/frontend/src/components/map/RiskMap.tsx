"use client";

import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import type { Zone } from "@/types";

interface RiskMapProps {
  zones: Zone[];
  selectedZoneId: number | null;
  clickedLocation?: { lat: number, lng: number } | null;
  filterRegion?: string | null;
  onSelectZone: (id: number) => void;
  onLocationSelect: (lat: number, lng: number) => void;
  onRegionSelect?: (region: string) => void;
  showRoadNetwork?: boolean;
  showRoadImpact?: boolean;
  roadImpactData?: any;
}

export default function RiskMap({ 
  zones, 
  selectedZoneId, 
  clickedLocation, 
  filterRegion, 
  onSelectZone, 
  onLocationSelect, 
  onRegionSelect,
  showRoadNetwork = false,
  showRoadImpact = false,
  roadImpactData = null
}: RiskMapProps) {
  const mapRef = useRef<L.Map | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const geojsonLayerRef = useRef<L.GeoJSON | null>(null);
  const pointsLayerRef = useRef<L.LayerGroup | null>(null);
  const roadNetworkLayerRef = useRef<L.GeoJSON | null>(null);
  const roadImpactLayerRef = useRef<L.GeoJSON | null>(null);
  const lastFittedRegionRef = useRef<string | null | undefined>(undefined);
  const lastRoadImpactDataRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      zoomControl: false,
      attributionControl: false,
    }).setView([26.2, 93.5], 7);

    // Standard OpenStreetMap base layer
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 12,
    }).addTo(map);

    L.control.zoom({ position: "topright" }).addTo(map);

    map.on("click", (e) => {
      onLocationSelect(e.latlng.lat, e.latlng.lng);
    });

    mapRef.current = map;
    pointsLayerRef.current = L.layerGroup().addTo(map);
    
    // Load GeoJSON once
    fetch("/ner_districts.json")
      .then(r => r.json())
      .then(data => {
        if (!mapRef.current) return;
        geojsonLayerRef.current = L.geoJSON(data, {
          style: () => ({
            fillColor: "#3A803B", // default low
            weight: 1,
            opacity: 0.8,
            color: '#ffffff',
            dashArray: '3',
            fillOpacity: 0.1
          })
        }).addTo(mapRef.current);
        
        // Trigger style update immediately if zones already exist
        updateMapLayers(zones, selectedZoneId, clickedLocation, filterRegion, showRoadNetwork, showRoadImpact, roadImpactData);
      });

    fetch("/ner_highways.geojson")
      .then(r => r.json())
      .then(data => {
        if (!mapRef.current) return;
        roadNetworkLayerRef.current = L.geoJSON(data, {
          style: () => ({
            color: "#A0AEC0",
            weight: 1.5,
            opacity: 0.6
          })
        });
        updateMapLayers(zones, selectedZoneId, clickedLocation, filterRegion, showRoadNetwork, showRoadImpact, roadImpactData);
      })
      .catch(e => console.error("Could not load road network", e));

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [onLocationSelect]);

  const updateMapLayers = (currentZones: Zone[], currentSelectedZoneId: number | null, currentClickedLoc?: {lat: number, lng: number} | null, currentFilterRegion?: string | null, showRoadNetwork?: boolean, showRoadImpact?: boolean, roadImpactData?: any) => {
    if (!mapRef.current || !geojsonLayerRef.current || !pointsLayerRef.current) return;

    // 1. Update GeoJSON District Colors based on Max Risk
    const districtRiskMap = new Map<string, number>();
    
    currentZones.forEach(z => {
      const existingMax = districtRiskMap.get(z.name) || 0;
      if (z.risk_score > existingMax) {
        districtRiskMap.set(z.name, z.risk_score);
      }
    });

    let boundsToFit: L.LatLngBounds | null = null;

    geojsonLayerRef.current.eachLayer((layer: any) => {
      const districtName = layer.feature?.properties?.NAME_2;
      let fillColor = "transparent";
      let borderColor = "#ffffff";
      let fillOpacity = 0.0;
      
      // If filtering by region, hide other regions
      if (currentFilterRegion && districtName !== currentFilterRegion) {
         layer.setStyle({ fillColor: "transparent", color: "transparent", fillOpacity: 0 });
         layer.off("click");
         return;
      }

      if (currentFilterRegion && districtName === currentFilterRegion) {
         boundsToFit = layer.getBounds();
      }
      
      if (districtName && districtRiskMap.has(districtName)) {
        const score = districtRiskMap.get(districtName)!;
        fillOpacity = 0.5;
        if (score >= 85) { fillColor = "#C93D33"; borderColor = "#8a2119"; }       // Critical (Red)
        else if (score >= 60) { fillColor = "#ea580c"; borderColor = "#9a3412"; }  // High (Deep Orange)
        else if (score >= 30) { fillColor = "#ca8a04"; borderColor = "#854d0e"; }  // Moderate (Deep Yellow)
        else { fillColor = "#3A803B"; borderColor = "#1b4d1c"; fillOpacity = 0.2; } // Low (Green)
        
        // Hide regional colors on the main map when road impact is toggled on to keep it clean
        if (!currentFilterRegion && showRoadImpact) {
           fillColor = "transparent";
           borderColor = "#A0AEC0"; // subtle grey border
           fillOpacity = 0.05;
        }
      }

      layer.setStyle({
        fillColor,
        fillOpacity,
        weight: 2,
        color: borderColor
      });
      
      // Add tooltip and click event to district
      if (districtName) {
         layer.bindTooltip(`<b>${districtName}</b><br/>Max Risk: ${districtRiskMap.get(districtName)?.toFixed(1) || 'N/A'}%`);
         layer.off("click"); // remove previous event listener
         layer.on("click", (e: any) => {
            L.DomEvent.stopPropagation(e);
            if (onRegionSelect) {
              onRegionSelect(districtName);
            }
         });
      }
    });

    if (boundsToFit && currentFilterRegion && currentFilterRegion !== lastFittedRegionRef.current) {
       mapRef.current.fitBounds(boundsToFit, { padding: [20, 20], maxZoom: 10 });
       lastFittedRegionRef.current = currentFilterRegion;
    } else if (currentFilterRegion === null && lastFittedRegionRef.current !== null) {
       lastFittedRegionRef.current = null;
    }

    // 2. Draw Points for precise locations
    const newPointsLayer = L.layerGroup();
    
    currentZones.forEach((zone) => {
      // If filtering by region, hide points outside region
      if (currentFilterRegion && zone.name !== currentFilterRegion) return;

      let color = "#3A803B";
      if (zone.risk_level === "critical") color = "#C93D33";
      else if (zone.risk_level === "high") color = "#ea580c";
      else if (zone.risk_level === "moderate") color = "#ca8a04";

      const isSelected = zone.id === currentSelectedZoneId;

      // Only highlight high/critical points or selected points to avoid clutter,
      // UNLESS we are focusing on a region, then show ALL points in that region.
      // Hide completely on main map if showRoadImpact is enabled.
      if (!currentFilterRegion && showRoadImpact) {
         return;
      }
      
      if (currentFilterRegion || zone.risk_level === "critical" || zone.risk_level === "high" || isSelected) {
        L.circleMarker([zone.lat, zone.lng], {
          radius: isSelected ? 8 : currentFilterRegion ? 6 : 4,
          fillColor: color,
          color: isSelected ? "#000" : "#fff",
          weight: isSelected ? 2 : 1,
          opacity: 1,
          fillOpacity: 0.9,
        })
        .bindTooltip(`<b>${zone.name}</b><br/>Risk: ${zone.risk_score.toFixed(1)}%`)
        .on("click", (e) => {
          L.DomEvent.stopPropagation(e);
          onSelectZone(zone.id);
        })
        .addTo(newPointsLayer);
      }
    });

    if (currentClickedLoc) {
      L.circleMarker([currentClickedLoc.lat, currentClickedLoc.lng], {
        radius: 6,
        fillColor: "#718096",
        color: "#1A202C",
        weight: 2,
        opacity: 1,
        fillOpacity: 1,
      })
      .bindTooltip(`<b>Location Outside NER</b><br/>No predictions`)
      .addTo(newPointsLayer);
    }

    if (pointsLayerRef.current) {
      mapRef.current.removeLayer(pointsLayerRef.current);
    }
    newPointsLayer.addTo(mapRef.current);
    pointsLayerRef.current = newPointsLayer;

    // Handle Road Network Layer
    if (showRoadNetwork && roadNetworkLayerRef.current) {
       if (!mapRef.current.hasLayer(roadNetworkLayerRef.current)) {
          roadNetworkLayerRef.current.addTo(mapRef.current);
       }
    } else if (roadNetworkLayerRef.current) {
       mapRef.current.removeLayer(roadNetworkLayerRef.current);
    }

    // Handle Potential Road Impact Layer
    if (showRoadImpact && roadImpactData) {
       // Only recreate if data reference changed or it doesn't exist
       if (!roadImpactLayerRef.current || roadImpactData !== lastRoadImpactDataRef.current) {
           if (roadImpactLayerRef.current) {
               mapRef.current.removeLayer(roadImpactLayerRef.current);
           }
           roadImpactLayerRef.current = L.geoJSON(roadImpactData, {
              style: (feature) => {
                 const impact = feature?.properties?.impact_level;
                 let color = "#A0AEC0";
                 let weight = 2;
                 if (impact === "critical") { color = "#C93D33"; weight = 4; }
                 else if (impact === "high") { color = "#ea580c"; weight = 4; }
                 else if (impact === "moderate") { color = "#ca8a04"; weight = 3; }
                 return { color, weight, opacity: 0.9 };
              },
              onEachFeature: (feature, layer) => {
                 const props = feature.properties;
                 const name = props?.name !== "Unknown Road" ? props?.name : props?.ref || "Road";
                 const impact = props?.impact_level?.toUpperCase();
                 if (impact !== "NO_DETECTED_IMPACT") {
                    layer.bindTooltip(`<b>${name}</b><br/>Status: POTENTIAL ROAD IMPACT<br/>Reason: Intersects ${props?.risk_level} risk area`);
                 }
              }
           });
           lastRoadImpactDataRef.current = roadImpactData;
       }
       if (!mapRef.current.hasLayer(roadImpactLayerRef.current)) {
           roadImpactLayerRef.current.addTo(mapRef.current);
       }
    } else if (roadImpactLayerRef.current) {
       mapRef.current.removeLayer(roadImpactLayerRef.current);
    }
  };

  useEffect(() => {
    updateMapLayers(zones, selectedZoneId, clickedLocation, filterRegion, showRoadNetwork, showRoadImpact, roadImpactData);
  }, [zones, selectedZoneId, clickedLocation, filterRegion, showRoadNetwork, showRoadImpact, roadImpactData]);

  return <div ref={containerRef} style={{ width: "100%", height: "100%", background: "#EAE4DB" }} />;
}
