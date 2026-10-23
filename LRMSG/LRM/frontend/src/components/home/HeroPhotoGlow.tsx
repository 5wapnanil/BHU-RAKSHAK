"use client";

import { useState, useCallback } from "react";
import Image from "next/image";
import { Eye, Shield, Compass, Sparkles } from "lucide-react";

export default function HeroPhotoGlow() {
  const [coords, setCoords] = useState<{ x: number; y: number }>({ x: 50, y: 50 });
  const [isHovered, setIsHovered] = useState(false);

  const handlePointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
    const y = Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100));
    setCoords({ x, y });
  }, []);

  const handlePointerEnter = useCallback(() => setIsHovered(true), []);
  const handlePointerLeave = useCallback(() => setIsHovered(false), []);

  return (
    <section
      aria-label="Terrain Observation Evidence Showcase"
      style={{
        padding: "0 5vw 64px",
        maxWidth: "1140px",
        margin: "0 auto",
      }}
    >
      <div
        className="hero-photo-card"
        onPointerMove={handlePointerMove}
        onPointerEnter={handlePointerEnter}
        onPointerLeave={handlePointerLeave}
        style={{
          position: "relative",
          borderRadius: "16px",
          backgroundColor: "var(--surface)",
          border: isHovered
            ? "1px solid rgba(139, 69, 19, 0.45)"
            : "1px solid var(--line)",
          boxShadow: isHovered
            ? "0 24px 48px -12px rgba(139, 69, 19, 0.22), 0 0 32px rgba(210, 153, 34, 0.22)"
            : "0 10px 30px -8px rgba(41, 37, 36, 0.08)",
          padding: "12px",
          overflow: "hidden",
          transition: "border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease",
          transform: isHovered ? "translateY(-2px)" : "translateY(0)",
          cursor: "default",
        }}
      >
        {/* Dynamic pointer-following radial glow spotlight */}
        <div
          aria-hidden="true"
          className="hero-glow-spotlight"
          style={{
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            zIndex: 3,
            borderRadius: "16px",
            background: `radial-gradient(circle 380px at ${coords.x}% ${coords.y}%, rgba(224, 90, 58, 0.32) 0%, rgba(210, 153, 34, 0.18) 35%, transparent 72%)`,
            opacity: isHovered ? 1 : 0,
            transition: "opacity 0.25s ease",
          }}
        />

        {/* Ambient border ring highlight */}
        <div
          aria-hidden="true"
          className="hero-glow-ambient"
          style={{
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            zIndex: 2,
            borderRadius: "16px",
            boxShadow: isHovered
              ? "inset 0 0 24px rgba(224, 90, 58, 0.15), 0 0 0 1px rgba(224, 90, 58, 0.35)"
              : "none",
            transition: "box-shadow 0.3s ease",
          }}
        />

        {/* Header Metadata Bar */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "8px",
            padding: "8px 12px 12px",
            borderBottom: "1px solid var(--line)",
            marginBottom: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                display: "inline-block",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: isHovered ? "var(--accent)" : "var(--green)",
                boxShadow: isHovered ? "0 0 8px var(--accent)" : "0 0 6px var(--green)",
                transition: "all 0.3s ease",
              }}
            />
            <span
              style={{
                font: "700 11px 'DM Mono'",
                letterSpacing: "1px",
                color: "var(--text-primary)",
                textTransform: "uppercase",
              }}
            >
              Geological Ground Evidence &bull; Active Field Observation
            </span>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "11px",
              fontFamily: "'DM Mono'",
              color: "var(--text-secondary)",
            }}
          >
            <Compass size={13} style={{ color: "var(--accent)" }} />
            <span>Uttarakhand Mountain Corridor &bull; Sector 7</span>
          </div>
        </div>

        {/* Photographic Evidence Container */}
        <div
          style={{
            position: "relative",
            width: "100%",
            height: "clamp(260px, 45vw, 440px)",
            borderRadius: "10px",
            overflow: "hidden",
            backgroundColor: "#292524",
          }}
        >
          <img
            src="/images/pahaarpulse-terrain.png"
            alt="PahaarPulse landslide monitoring and terrain observation evidence"
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              objectPosition: "center",
              display: "block",
              transition: "transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), filter 0.3s ease",
              transform: isHovered ? "scale(1.025)" : "scale(1)",
              filter: isHovered ? "brightness(1.04) contrast(1.02)" : "brightness(0.96) contrast(1)",
            }}
          />

          {/* Photographic Watermark / Overlay Gradient */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "linear-gradient(180deg, rgba(41, 37, 36, 0.1) 0%, rgba(41, 37, 36, 0.4) 65%, rgba(41, 37, 36, 0.85) 100%)",
              pointerEvents: "none",
            }}
          />

          {/* Embedded Evidence Badges */}
          <div
            style={{
              position: "absolute",
              bottom: "16px",
              left: "16px",
              right: "16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-end",
              flexWrap: "wrap",
              gap: "12px",
              pointerEvents: "none",
            }}
          >
            <div style={{ maxWidth: "600px" }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  backgroundColor: "rgba(0, 0, 0, 0.65)",
                  backdropFilter: "blur(6px)",
                  border: "1px solid rgba(255, 255, 255, 0.15)",
                  color: "#ffffff",
                  font: "700 10px 'DM Mono'",
                  letterSpacing: "0.5px",
                  marginBottom: "6px",
                }}
              >
                <Eye size={12} style={{ color: "var(--amber)" }} />
                <span>TERRAIN STABILIZATION BENCHMARK</span>
              </div>
              <p
                style={{
                  font: "400 13px/1.4 'DM Sans'",
                  color: "rgba(255, 255, 255, 0.92)",
                  margin: 0,
                  textShadow: "0 1px 3px rgba(0, 0, 0, 0.8)",
                }}
              >
                Photographic slope documentation captures micro-fractures, talus deposition, and drainage anomalies before major road blockages occur.
              </p>
            </div>

            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "4px",
                backgroundColor: isHovered ? "rgba(139, 69, 19, 0.85)" : "rgba(41, 37, 36, 0.75)",
                backdropFilter: "blur(6px)",
                border: "1px solid rgba(255, 255, 255, 0.2)",
                color: "#ffffff",
                font: "700 11px 'DM Mono'",
                letterSpacing: "0.5px",
                transition: "background-color 0.3s ease",
              }}
            >
              <Sparkles size={12} style={{ color: isHovered ? "#fbbf24" : "var(--amber)" }} />
              <span>{isHovered ? "HOVER GLOW ACTIVE" : "FIELD LOG #PP-2026-NE"}</span>
            </div>
          </div>
        </div>

        {/* Footer Technical Metadata */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
            padding: "12px 8px 4px",
            fontSize: "11px",
            fontFamily: "'DM Mono'",
            color: "var(--text-secondary)",
          }}
        >
          <div>
            Observation Ground-Truth Verification &bull; Multi-Resolution Slope Profile
          </div>
          <div style={{ display: "flex", gap: "16px" }}>
            <span>Lat: <strong>30.3165° N</strong></span>
            <span>Lng: <strong>78.0322° E</strong></span>
            <span>Status: <strong style={{ color: "var(--green)" }}>MONITORED</strong></span>
          </div>
        </div>
      </div>
    </section>
  );
}
