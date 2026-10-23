"use client";

import Link from "next/link";
import { getFeaturedArticles } from "@/data/articles";
import { ArticleCard } from "./ArticleCard";
import { Motion } from "@/components/ui/Motion";
import { fadeInUp, staggerContainer, cardReveal } from "@/animations/variants";

export function InsightsSection() {
  const featured = getFeaturedArticles();

  return (
    <div>
      <Motion initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={fadeInUp}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">RESEARCH &amp; INSIGHTS</p>
            <h2>Understanding the forces behind landslide risk.</h2>
          </div>
        </div>
      </Motion>

      <Motion initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={fadeInUp} transition={{ delay: 0.1 }}>
        <p style={{ fontSize: "13px", fontFamily: "'DM Sans', sans-serif", color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: "24px", maxWidth: "700px" }}>
          Explore the science, environmental signals, GIS technologies, and machine-learning approaches behind modern landslide risk assessment and monitoring.
        </p>
      </Motion>

      <Motion initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }} variants={staggerContainer}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px", marginBottom: "24px" }}>
          {featured.map((article) => (
            <Motion key={article.id} variants={cardReveal}>
              <ArticleCard article={article} />
            </Motion>
          ))}
        </div>
      </Motion>

      <Motion initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fadeInUp}>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <Link
            href="/insights"
            style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: "1px",
              padding: "12px 24px",
              background: "var(--paper)",
              color: "var(--text-primary)",
              border: "1px solid var(--line)",
              borderRadius: "3px",
              textDecoration: "none",
              cursor: "pointer",
            }}
          >
            VIEW MORE →
          </Link>
        </div>
      </Motion>
    </div>
  );
}
