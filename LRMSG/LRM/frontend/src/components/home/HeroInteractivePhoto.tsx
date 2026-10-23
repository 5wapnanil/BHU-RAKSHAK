"use client";

import { useState, useCallback, useRef } from "react";
import { MapPin, Maximize2, X, Compass, ExternalLink } from "lucide-react";

export default function HeroInteractivePhoto() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [coords, setCoords] = useState<{ x: number; y: number }>({ x: 50, y: 50 });
  const [isHovered, setIsHovered] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handlePointerMove = useCallback((e: React.PointerEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
    const y = Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100));
    setCoords({ x, y });
  }, []);

  const handlePointerEnter = useCallback(() => setIsHovered(true), []);
  const handlePointerLeave = useCallback(() => {
    setIsHovered(false);
    setCoords({ x: 50, y: 50 });
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", maxWidth: "560px", margin: "0 auto" }}>
      {/* Outer Glow Halo behind Card */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: "-8px",
          borderRadius: "32px",
          background: isHovered
            ? "radial-gradient(circle at 60% 50%, rgba(245, 158, 11, 0.45) 0%, rgba(217, 83, 30, 0.35) 45%, transparent 75%)"
            : "radial-gradient(circle at 60% 50%, rgba(245, 158, 11, 0.28) 0%, rgba(217, 83, 30, 0.18) 45%, transparent 75%)",
          filter: "blur(20px)",
          opacity: 0.9,
          pointerEvents: "none",
          transition: "background 0.3s ease, opacity 0.3s ease",
          zIndex: 1,
        }}
      />

      {/* Main Photographic Card */}
      <div
        ref={containerRef}
        className="hero-interactive-card"
        onPointerMove={handlePointerMove}
        onPointerEnter={handlePointerEnter}
        onPointerLeave={handlePointerLeave}
        style={{
          position: "relative",
          zIndex: 2,
          borderRadius: "24px",
          backgroundColor: "#221E1F",
          overflow: "hidden",
          border: isHovered
            ? "2px solid rgba(245, 158, 11, 0.95)"
            : "1.5px solid rgba(245, 158, 11, 0.65)",
          boxShadow: isHovered
            ? "0 0 0 1px rgba(245, 158, 11, 0.8), 0 20px 45px -10px rgba(189, 83, 46, 0.35), 0 0 50px rgba(245, 158, 11, 0.4)"
            : "0 0 0 1px rgba(245, 158, 11, 0.3), 0 14px 35px -8px rgba(189, 83, 46, 0.2), 0 0 30px rgba(245, 158, 11, 0.25)",
          aspectRatio: "16 / 10.5",
          transition: "border-color 0.25s ease, box-shadow 0.25s ease, transform 0.25s ease",
          transform: isHovered ? "translateY(-2px)" : "translateY(0)",
          cursor: "pointer",
        }}
        onClick={() => setIsModalOpen(true)}
        role="button"
        tabIndex={0}
        aria-label="View high resolution field evidence photograph"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setIsModalOpen(true);
          }
        }}
      >
        {/* Real Mountain Landslide Road Photograph */}
        <img
          src="/images/hero-landslide-road.jpg"
          alt="Field evidence photograph showing a severe slope failure and rockfall debris obstructing a mountain roadway in Nagaland, India"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center 42%",
            display: "block",
            transition: "transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), filter 0.3s ease",
            transform: isHovered ? "scale(1.025)" : "scale(1)",
            filter: isHovered ? "brightness(1.03) contrast(1.02)" : "brightness(0.97) contrast(1)",
          }}
        />

        {/* Pointer-Following Radial Glow Spotlight */}
        <div
          aria-hidden="true"
          className="hero-spotlight-layer"
          style={{
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            zIndex: 3,
            background: `radial-gradient(circle 340px at ${coords.x}% ${coords.y}%, rgba(245, 158, 11, 0.42) 0%, rgba(217, 83, 30, 0.22) 40%, transparent 72%)`,
            opacity: isHovered ? 1 : 0.4,
            transition: "opacity 0.25s ease",
          }}
        />

        {/* Ambient Top & Bottom Vignette Overlays for Maximum Legibility */}
        <div
          aria-hidden="true"
          style={{
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            zIndex: 2,
            background:
              "linear-gradient(180deg, rgba(20, 18, 16, 0.35) 0%, transparent 35%, transparent 60%, rgba(20, 18, 16, 0.8) 100%)",
          }}
        />

        {/* Top-Right Expand Affordance */}
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setIsModalOpen(true);
          }}
          aria-label="Expand image"
          style={{
            position: "absolute",
            top: "14px",
            right: "14px",
            zIndex: 4,
            width: "34px",
            height: "34px",
            borderRadius: "50%",
            backgroundColor: "rgba(22, 19, 18, 0.7)",
            backdropFilter: "blur(8px)",
            border: "1px solid rgba(255, 255, 255, 0.25)",
            color: "#ffffff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            transition: "transform 0.15s ease, background-color 0.15s ease",
            transform: isHovered ? "scale(1.08)" : "scale(1)",
          }}
        >
          <Maximize2 size={15} />
        </button>

        {/* Bottom-Left Verified Location Pill */}
        <div
          style={{
            position: "absolute",
            bottom: "16px",
            left: "16px",
            zIndex: 4,
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "8px 14px",
            borderRadius: "10px",
            backgroundColor: "rgba(22, 19, 18, 0.82)",
            backdropFilter: "blur(10px)",
            border: "1px solid rgba(255, 255, 255, 0.18)",
            boxShadow: "0 4px 16px rgba(0, 0, 0, 0.35)",
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              backgroundColor: "rgba(245, 158, 11, 0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <MapPin size={15} style={{ color: "#F59E0B" }} />
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span
              style={{
                font: "700 12px 'Space Grotesk', sans-serif",
                color: "#ffffff",
                letterSpacing: "-0.2px",
                lineHeight: 1.2,
              }}
            >
              Real field evidence
            </span>
            <span
              style={{
                font: "400 11px 'DM Sans', sans-serif",
                color: "rgba(240, 235, 228, 0.85)",
                lineHeight: 1.2,
                marginTop: "2px",
              }}
            >
              Landslide-affected slope &bull; Nagaland, India
            </span>
          </div>
        </div>
      </div>

      {/* Hand-Drawn "Hover to explore field evidence" Annotation Arrow */}
      <div
        className="hero-hover-hint"
        aria-hidden="true"
        style={{
          position: "absolute",
          bottom: "-38px",
          right: "12px",
          zIndex: 5,
          display: "flex",
          alignItems: "center",
          gap: "8px",
          pointerEvents: "none",
          opacity: isHovered ? 0.95 : 0.75,
          transform: isHovered ? "translateX(2px)" : "translateX(0)",
          transition: "opacity 0.25s ease, transform 0.25s ease",
        }}
      >
        <svg width="34" height="26" viewBox="0 0 34 26" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M2 22C12 24 24 16 28 4M28 4L22 7M28 4L31 11"
            stroke="#9C411E"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <span
          style={{
            fontFamily: "cursive, 'Caveat', 'Segoe Script', 'DM Sans', sans-serif",
            fontStyle: "italic",
            fontSize: "13px",
            color: "#9C411E",
            fontWeight: 600,
            letterSpacing: "0.2px",
            whiteSpace: "nowrap",
          }}
        >
          Hover to explore field evidence
        </span>
      </div>

      {/* Accessible Fullscreen Modal */}
      {isModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="High Resolution Field Evidence Image"
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            backgroundColor: "rgba(18, 16, 14, 0.88)",
            backdropFilter: "blur(12px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "24px",
          }}
          onClick={() => setIsModalOpen(false)}
        >
          <div
            style={{
              position: "relative",
              maxWidth: "1000px",
              width: "100%",
              backgroundColor: "#201C1A",
              borderRadius: "16px",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              overflow: "hidden",
              boxShadow: "0 25px 60px rgba(0, 0, 0, 0.6)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "16px 20px",
                borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
              }}
            >
              <div>
                <h3 style={{ font: "700 15px 'Space Grotesk'", color: "#ffffff", margin: 0 }}>
                  Field Observation Evidence &bull; Slope Failure &amp; Talus Deposition
                </h3>
                <p style={{ font: "400 12px 'DM Sans'", color: "rgba(255, 255, 255, 0.65)", margin: "4px 0 0" }}>
                  Verified geological evidence: Nagaland, India (CC BY-SA 4.0 &bull; Ganesh Mohan T)
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                aria-label="Close image modal"
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#ffffff",
                  cursor: "pointer",
                  padding: "6px",
                  borderRadius: "6px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ maxHeight: "70vh", overflow: "hidden", backgroundColor: "#000000" }}>
              <img
                src="/images/hero-landslide-road.jpg"
                alt="Full resolution field observation of landslide on mountain roadway"
                style={{
                  width: "100%",
                  height: "auto",
                  maxHeight: "70vh",
                  objectFit: "contain",
                  display: "block",
                  margin: "0 auto",
                }}
              />
            </div>

            <div
              style={{
                padding: "14px 20px",
                backgroundColor: "rgba(0, 0, 0, 0.3)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "12px",
                fontSize: "11px",
                fontFamily: "'DM Mono', monospace",
                color: "rgba(255, 255, 255, 0.7)",
              }}
            >
              <span>Captured in the Himalayan / Patkai mountain system</span>
              <a
                href="https://commons.wikimedia.org/wiki/File:Landslide_in_Nagaland_01.jpg"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                  color: "#F59E0B",
                  textDecoration: "none",
                }}
              >
                <span>View Wikimedia Commons Record</span>
                <ExternalLink size={12} />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
