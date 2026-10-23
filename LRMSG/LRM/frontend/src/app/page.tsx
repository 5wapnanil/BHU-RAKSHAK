import Link from "next/link";
import TopographicContourLines from "@/components/home/TopographicContourLines";
import HeroInteractivePhoto from "@/components/home/HeroInteractivePhoto";
import HowItWorksSection from "@/components/home/HowItWorksSection";
import BottomMountainPanorama from "@/components/home/BottomMountainPanorama";
import {
  FileText,
  LayoutGrid,
  ArrowRight,
  Camera,
  MapPin,
  ShieldCheck,
  Mountain,
} from "lucide-react";

const CAPABILITIES = [
  {
    icon: Camera,
    label: "Photo-based observations",
  },
  {
    icon: MapPin,
    label: "Location & timestamp capture",
  },
  {
    icon: FileText,
    label: "Structured report generation",
  },
  {
    icon: ShieldCheck,
    label: "Administrative review & tracking",
  },
];

export default function HomePage() {
  return (
    <main
      style={{
        position: "relative",
        minHeight: "calc(100vh - 64px)",
        backgroundColor: "#F5EEE6",
        color: "#231F20",
        overflowX: "hidden",
      }}
    >
      {/* ── TOPOGRAPHIC CONTOUR LINES (BACKGROUND DECORATION) ── */}
      <TopographicContourLines />

      {/* ── TWO-COLUMN HERO SECTION ── */}
      <section
        style={{
          position: "relative",
          zIndex: 1,
          maxWidth: "1200px",
          margin: "0 auto",
          padding: "56px 5vw 48px",
        }}
      >
        <div className="hero-two-col">
          {/* Left Column: Headline, Actions, Capabilities */}
          <div>
            {/* Eyebrow */}
            <div style={{ marginBottom: "16px" }}>
              <span
                style={{
                  font: "700 11px 'DM Mono', monospace",
                  letterSpacing: "1.2px",
                  color: "#8E3A1A",
                  textTransform: "uppercase",
                }}
              >
                FIELD OBSERVATION &amp; VERIFICATION PLATFORM
              </span>
            </div>

            {/* Main Headline */}
            <h1
              style={{
                font: "700 clamp(34px, 4.2vw, 54px)/1.12 'Space Grotesk', sans-serif",
                letterSpacing: "-1px",
                color: "#231F20",
                margin: "0 0 20px",
                maxWidth: "600px",
              }}
            >
              Turn Field Evidence Into Actionable{" "}
              <span style={{ color: "#BD532E" }}>Landslide Reports</span>
            </h1>

            {/* Supporting Paragraph */}
            <p
              style={{
                font: "400 clamp(14px, 1.8vw, 16px)/1.6 'DM Sans', sans-serif",
                color: "#736B63",
                margin: "0 0 32px",
                maxWidth: "520px",
              }}
            >
              Collect ground evidence of potential slope instability, organize field observations into structured reports, and enable authorities to inspect evidence and guide appropriate follow-up.
            </p>

            {/* Two Prominent Action Buttons */}
            <div
              style={{
                display: "flex",
                gap: "14px",
                flexWrap: "wrap",
                alignItems: "center",
                marginBottom: "36px",
              }}
            >
              {/* Primary Action Button */}
              <Link
                href="/report"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "14px 24px",
                  borderRadius: "8px",
                  backgroundColor: "#9C411E",
                  color: "#ffffff",
                  font: "700 13px 'DM Sans', sans-serif",
                  letterSpacing: "0.3px",
                  textDecoration: "none",
                  boxShadow: "0 6px 18px rgba(156, 65, 30, 0.28)",
                  transition: "background-color 0.15s ease, transform 0.15s ease",
                }}
              >
                <FileText size={17} />
                <span>Submit a Field Report</span>
                <ArrowRight size={15} />
              </Link>

              {/* Secondary Action Button */}
              <Link
                href="/dashboard"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "14px 22px",
                  borderRadius: "8px",
                  backgroundColor: "#FAF6F0",
                  color: "#231F20",
                  border: "1px solid #D8CABA",
                  font: "700 13px 'DM Sans', sans-serif",
                  letterSpacing: "0.3px",
                  textDecoration: "none",
                  boxShadow: "0 2px 6px rgba(0, 0, 0, 0.04)",
                  transition: "background-color 0.15s ease, border-color 0.15s ease",
                }}
              >
                <LayoutGrid size={16} style={{ color: "#736B63" }} />
                <span>View Admin Panel</span>
              </Link>
            </div>

            {/* Four Compact Capability Indicators */}
            <div
              className="capabilities-row"
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                gap: "12px",
                paddingTop: "24px",
                borderTop: "1px solid rgba(220, 208, 196, 0.7)",
                maxWidth: "580px",
              }}
            >
              {CAPABILITIES.map((cap) => {
                const Icon = cap.icon;
                return (
                  <div
                    key={cap.label}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <div
                      style={{
                        width: "32px",
                        height: "32px",
                        borderRadius: "50%",
                        backgroundColor: "#EFE4D6",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      <Icon size={15} style={{ color: "#8E3A1A" }} />
                    </div>
                    <span
                      style={{
                        font: "500 11px/1.3 'DM Sans', sans-serif",
                        color: "#685F56",
                      }}
                    >
                      {cap.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Hero Photograph & Interactive Glow */}
          <div style={{ display: "flex", justifyContent: "center" }}>
            <HeroInteractivePhoto />
          </div>
        </div>
      </section>

      {/* ── THREE-STAGE REPORTING LIFECYCLE ("HOW IT WORKS") ── */}
      <HowItWorksSection />

      {/* ── BOTTOM MOUNTAIN PANORAMA & BENEFITS STRIP ── */}
      <BottomMountainPanorama />

      {/* ── MINIMALIST FOOTER ── */}
      <footer
        style={{
          borderTop: "1px solid rgba(214, 204, 194, 0.6)",
          backgroundColor: "#EDE4DA",
          padding: "32px 5vw",
          fontSize: "12px",
          color: "#787067",
        }}
      >
        <div
          style={{
            maxWidth: "1200px",
            margin: "0 auto",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Mountain size={16} style={{ color: "#8E3A1A" }} />
            <span style={{ font: "700 13px 'Space Grotesk'", color: "#231F20" }}>PahaarPulse</span>
            <span style={{ font: "500 11px 'DM Mono'", color: "#8E3A1A" }}>FIELD INTELLIGENCE</span>
          </div>

          <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
            <Link href="/" style={{ color: "#736B63", textDecoration: "none" }}>
              Home
            </Link>
            <Link href="/report" style={{ color: "#736B63", textDecoration: "none" }}>
              Field Report
            </Link>
            <Link href="/dashboard" style={{ color: "#736B63", textDecoration: "none" }}>
              Admin Panel
            </Link>
            <Link href="/dashboard/reports" style={{ color: "#736B63", textDecoration: "none" }}>
              Reports Registry
            </Link>
            <Link href="/dashboard/map" style={{ color: "#736B63", textDecoration: "none" }}>
              Observation Map
            </Link>
          </div>

          <div style={{ font: "400 11px 'DM Sans'", color: "#8A8178" }}>
            &copy; 2026 PahaarPulse. Landslide Field-Intelligence &bull; Himalayan Terrain Observation.
          </div>
        </div>
      </footer>
    </main>
  );
}
