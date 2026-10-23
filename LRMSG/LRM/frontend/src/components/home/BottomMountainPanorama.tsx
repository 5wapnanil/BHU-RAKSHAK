import { Mountain, Users, Leaf, ShieldCheck } from "lucide-react";

const BENEFITS = [
  {
    title: "Safer Communities",
    description: "Through better field intelligence",
    icon: Mountain,
  },
  {
    title: "Collaborative Response",
    description: "Evidence for informed decisions",
    icon: Users,
  },
  {
    title: "Mountain-Focused",
    description: "Built for hilly and landslide-prone regions",
    icon: Leaf,
  },
  {
    title: "Responsible AI",
    description: "Human review always required",
    icon: ShieldCheck,
  },
];

export default function BottomMountainPanorama() {
  return (
    <section
      aria-label="Environmental Context and Operational Pillars"
      style={{
        position: "relative",
        width: "100%",
        paddingTop: "40px",
        paddingBottom: "48px",
        overflow: "hidden",
      }}
    >
      {/* Background Himalayan Panorama Container */}
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: "url('/images/bottom-himalaya-dusk.jpg')",
          backgroundSize: "cover",
          backgroundPosition: "center 65%",
          backgroundRepeat: "no-repeat",
          zIndex: 0,
        }}
      >
        {/* Top Gradient Blend transitioning from #F5EEE6 down into the photograph */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "linear-gradient(180deg, #F5EEE6 0%, rgba(245, 238, 230, 0.75) 18%, rgba(245, 238, 230, 0.25) 45%, rgba(20, 18, 16, 0.6) 100%)",
          }}
        />
      </div>

      {/* Floating Translucent Benefits Strip */}
      <div
        style={{
          position: "relative",
          zIndex: 1,
          maxWidth: "1140px",
          margin: "80px auto 0",
          padding: "0 5vw",
        }}
      >
        <div
          className="benefits-strip-container"
          style={{
            backgroundColor: "rgba(248, 242, 234, 0.88)",
            backdropFilter: "blur(16px)",
            WebkitBackdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.65)",
            borderRadius: "18px",
            padding: "24px 28px",
            boxShadow: "0 16px 40px -10px rgba(25, 20, 16, 0.22)",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
            gap: "24px",
            alignItems: "center",
          }}
        >
          {BENEFITS.map((benefit, idx) => {
            const Icon = benefit.icon;
            return (
              <div
                key={benefit.title}
                className="benefit-item"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "14px",
                  paddingRight: idx < BENEFITS.length - 1 ? "16px" : 0,
                  borderRight: idx < BENEFITS.length - 1 ? "1px solid rgba(214, 204, 194, 0.5)" : "none",
                }}
              >
                {/* Circular Icon Badge */}
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "50%",
                    backgroundColor: "#EFE4D6",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <Icon size={20} style={{ color: "#8E3A1A" }} />
                </div>

                {/* Text Content */}
                <div>
                  <h4
                    style={{
                      font: "700 14px 'Space Grotesk', sans-serif",
                      color: "#231F20",
                      margin: "0 0 2px",
                      letterSpacing: "-0.2px",
                      lineHeight: 1.2,
                    }}
                  >
                    {benefit.title}
                  </h4>
                  <p
                    style={{
                      font: "400 12px/1.35 'DM Sans', sans-serif",
                      color: "#736B63",
                      margin: 0,
                    }}
                  >
                    {benefit.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Scenic Location & Attribution Caption */}
        <div
          style={{
            marginTop: "16px",
            textAlign: "center",
            fontSize: "11px",
            fontFamily: "'DM Mono', monospace",
            color: "rgba(255, 255, 255, 0.85)",
            textShadow: "0 1px 3px rgba(0, 0, 0, 0.75)",
          }}
        >
          Himalayan Mountain Panorama &bull; Mussoorie, Uttarakhand &bull; Yamunotri &amp; Bandarpoonch Peaks
        </div>
      </div>
    </section>
  );
}
