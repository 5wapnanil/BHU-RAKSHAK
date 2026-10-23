"use client";

import { useEffect, useRef, useCallback } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export default function MapBackground() {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const posRef = useRef({ x: 0, y: 0 });
  const rafRef = useRef(0);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;
    const map = L.map(mapRef.current, {
      center: [25.8, 93.5],
      zoom: 7,
      zoomControl: false,
      attributionControl: false,
      dragging: false,
      scrollWheelZoom: false,
      doubleClickZoom: false,
      touchZoom: false,
      keyboard: false,
      minZoom: 6,
      maxZoom: 10,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
    }).addTo(map);

    const riskSpots: [number, number, string, number][] = [
      [27.04, 88.26, "#DC2626", 35],
      [27.33, 88.61, "#D29922", 28],
      [25.57, 91.89, "#DC2626", 32],
      [25.67, 94.11, "#D29922", 24],
      [23.73, 92.72, "#D29922", 26],
      [24.81, 93.94, "#DC2626", 30],
      [26.14, 91.74, "#3FB950", 20],
      [27.48, 94.90, "#D29922", 22],
      [23.83, 91.29, "#3FB950", 18],
      [25.48, 93.15, "#DC2626", 28],
      [26.75, 94.22, "#D29922", 24],
      [24.48, 93.55, "#DC2626", 32],
    ];

    riskSpots.forEach(([lat, lng, color, radius]) => {
      const outer = L.circleMarker([lat, lng], {
        radius: radius,
        fillColor: color,
        fillOpacity: 0.12,
        stroke: false,
        interactive: false,
      }).addTo(map);

      const inner = L.circleMarker([lat, lng], {
        radius: 6,
        fillColor: color,
        fillOpacity: 0.85,
        color: color,
        weight: 2,
        opacity: 0.9,
        interactive: false,
      }).addTo(map);

      const pulse = L.circleMarker([lat, lng], {
        radius: 6,
        fillColor: color,
        fillOpacity: 0.4,
        stroke: false,
        interactive: false,
      }).addTo(map);

      let t = 0;
      const tick = () => {
        t += 0.03;
        const s = 1 + Math.sin(t) * 0.8;
        const o = 0.4 - Math.sin(t) * 0.25;
        pulse.setStyle({ radius: 6 * s, fillOpacity: Math.max(0.05, o) });
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });

    mapInstanceRef.current = map;
    return () => {
      try { map.stop(); map.remove(); mapInstanceRef.current = null; } catch {}
    };
  }, []);

  const update = useCallback(() => {
    if (mapRef.current) {
      mapRef.current.style.setProperty("--mx", `${posRef.current.x}px`);
      mapRef.current.style.setProperty("--my", `${posRef.current.y}px`);
    }
    rafRef.current = 0;
  }, []);

  useEffect(() => {
    const heroEl = document.querySelector(".hero") as HTMLElement | null;
    const onMove = (e: MouseEvent) => {
      posRef.current = { x: e.clientX, y: e.clientY };
      if (!rafRef.current) rafRef.current = requestAnimationFrame(update);

      if (mapRef.current) {
        if (heroEl) {
          const r = heroEl.getBoundingClientRect();
          const inHero = e.clientY >= r.top && e.clientY <= r.bottom;
          mapRef.current.style.opacity = inHero ? "1" : "0";
        }
      }
    };
    const onLeave = () => {
      if (mapRef.current) mapRef.current.style.opacity = "0";
    };

    document.addEventListener("mousemove", onMove, { passive: true });
    document.documentElement.addEventListener("mouseleave", onLeave);
    return () => {
      cancelAnimationFrame(rafRef.current);
      document.removeEventListener("mousemove", onMove);
      document.documentElement.removeEventListener("mouseleave", onLeave);
    };
  }, [update]);

  return (
    <div
      ref={mapRef}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 0,
        pointerEvents: "none",
        opacity: 0,
        transition: "opacity 0.3s ease",
        maskImage:
          "radial-gradient(circle 420px at var(--mx, 50%) var(--my, 50%), " +
          "black 0%, black 6%, " +
          "rgba(0,0,0,0.97) 10%, rgba(0,0,0,0.92) 14%, " +
          "rgba(0,0,0,0.84) 18%, rgba(0,0,0,0.75) 22%, " +
          "rgba(0,0,0,0.65) 27%, rgba(0,0,0,0.54) 32%, " +
          "rgba(0,0,0,0.44) 37%, rgba(0,0,0,0.35) 42%, " +
          "rgba(0,0,0,0.27) 47%, rgba(0,0,0,0.20) 52%, " +
          "rgba(0,0,0,0.14) 58%, rgba(0,0,0,0.09) 64%, " +
          "rgba(0,0,0,0.05) 71%, rgba(0,0,0,0.03) 78%, " +
          "rgba(0,0,0,0.01) 86%, transparent 100%)",
        WebkitMaskImage:
          "radial-gradient(circle 420px at var(--mx, 50%) var(--my, 50%), " +
          "black 0%, black 6%, " +
          "rgba(0,0,0,0.97) 10%, rgba(0,0,0,0.92) 14%, " +
          "rgba(0,0,0,0.84) 18%, rgba(0,0,0,0.75) 22%, " +
          "rgba(0,0,0,0.65) 27%, rgba(0,0,0,0.54) 32%, " +
          "rgba(0,0,0,0.44) 37%, rgba(0,0,0,0.35) 42%, " +
          "rgba(0,0,0,0.27) 47%, rgba(0,0,0,0.20) 52%, " +
          "rgba(0,0,0,0.14) 58%, rgba(0,0,0,0.09) 64%, " +
          "rgba(0,0,0,0.05) 71%, rgba(0,0,0,0.03) 78%, " +
          "rgba(0,0,0,0.01) 86%, transparent 100%)",
      }}
    />
  );
}
