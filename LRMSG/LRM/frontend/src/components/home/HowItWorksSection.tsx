import { Camera, Brain, Users, ArrowRight } from "lucide-react";

const STEPS = [
  {
    step: 1,
    title: "Capture",
    description: "Upload a photograph and describe the observed conditions in the field.",
    icon: Camera,
    badge: null,
  },
  {
    step: 2,
    title: "Analyze",
    description: "Generate structured preliminary observations using AI (coming soon).",
    icon: Brain,
    badge: "COMING SOON",
  },
  {
    step: 3,
    title: "Review",
    description: "Administrators inspect the evidence and record a human review decision.",
    icon: Users,
    badge: null,
  },
];

export default function HowItWorksSection() {
  return (
    <section
      aria-labelledby="how-it-works-title"
      style={{
        maxWidth: "1200px",
        margin: "0 auto",
        padding: "0 5vw 48px",
      }}
    >
      <div
        className="how-it-works-container"
        style={{
          backgroundColor: "#FAF5EE",
          border: "1px solid #E6D8C8",
          borderRadius: "24px",
          padding: "48px 40px",
          boxShadow: "0 10px 30px rgba(44, 38, 30, 0.04)",
        }}
      >
        {/* Section Heading */}
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <h2
            id="how-it-works-title"
            style={{
              font: "700 clamp(24px, 3.5vw, 32px) 'Space Grotesk', sans-serif",
              letterSpacing: "-0.5px",
              color: "#231F20",
              margin: "0 0 8px",
            }}
          >
            How It Works
          </h2>
          <p
            style={{
              font: "400 clamp(13px, 1.8vw, 15px) 'DM Sans', sans-serif",
              color: "#787067",
              margin: 0,
            }}
          >
            A simple workflow from field observation to authoritative follow-up.
          </p>
        </div>

        {/* Three Horizontal Steps */}
        <div
          className="how-it-works-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "1fr auto 1fr auto 1fr",
            alignItems: "center",
            gap: "16px",
          }}
        >
          {STEPS.map((stepItem, index) => {
            const Icon = stepItem.icon;
            return (
              <div key={stepItem.step} style={{ display: "contents" }}>
                {/* Step Card */}
                <div
                  className="how-it-works-step-card"
                  style={{
                    position: "relative",
                    display: "flex",
                    alignItems: "flex-start",
                    gap: "18px",
                    padding: "20px 24px",
                    borderRadius: "16px",
                    backgroundColor: "rgba(255, 255, 255, 0.65)",
                    border: "1px solid rgba(230, 216, 200, 0.8)",
                    minHeight: "130px",
                  }}
                >
                  {/* Step Number Badge */}
                  <div
                    style={{
                      position: "absolute",
                      top: "14px",
                      left: "14px",
                      width: "22px",
                      height: "22px",
                      borderRadius: "50%",
                      backgroundColor: "#8E3A1A",
                      color: "#ffffff",
                      font: "700 11px 'Space Grotesk', sans-serif",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      zIndex: 2,
                    }}
                  >
                    {stepItem.step}
                  </div>

                  {/* Circular Icon Container */}
                  <div
                    style={{
                      width: "60px",
                      height: "60px",
                      borderRadius: "50%",
                      backgroundColor: "#EFE4D6",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      flexShrink: 0,
                      marginTop: "6px",
                    }}
                  >
                    <Icon size={26} style={{ color: "#8E3A1A" }} />
                  </div>

                  {/* Step Content */}
                  <div style={{ flex: 1, paddingTop: "4px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <h3
                        style={{
                          font: "700 17px 'Space Grotesk', sans-serif",
                          color: "#231F20",
                          margin: 0,
                          letterSpacing: "-0.2px",
                        }}
                      >
                        {stepItem.title}
                      </h3>
                      {stepItem.badge && (
                        <span
                          style={{
                            fontSize: "9px",
                            fontFamily: "'DM Mono', monospace",
                            fontWeight: 700,
                            letterSpacing: "0.5px",
                            padding: "2px 6px",
                            borderRadius: "3px",
                            backgroundColor: "rgba(142, 58, 26, 0.12)",
                            color: "#8E3A1A",
                            border: "1px solid rgba(142, 58, 26, 0.25)",
                          }}
                        >
                          {stepItem.badge}
                        </span>
                      )}
                    </div>
                    <p
                      style={{
                        font: "400 13px/1.5 'DM Sans', sans-serif",
                        color: "#736B63",
                        margin: 0,
                      }}
                    >
                      {stepItem.description}
                    </p>
                  </div>
                </div>

                {/* Arrow Connector between steps */}
                {index < STEPS.length - 1 && (
                  <div
                    className="how-it-works-arrow"
                    aria-hidden="true"
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "#9C411E",
                      opacity: 0.7,
                      padding: "0 4px",
                    }}
                  >
                    <ArrowRight size={22} strokeWidth={2} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
