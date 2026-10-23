"use client";

import Link from "next/link";
import type { Article } from "@/data/articles";

export function ArticleCard({ article }: { article: Article }) {
  return (
    <article className="card" style={{ borderTop: "3px solid var(--accent)", display: "flex", flexDirection: "column", gap: "12px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "10px", fontWeight: 700, color: "var(--accent-text)", fontFamily: "'DM Mono', monospace", letterSpacing: "0.5px" }}>
          {article.category}
        </span>
        <span style={{ fontSize: "9px", fontWeight: 500, color: "var(--text-secondary)", fontFamily: "'DM Mono', monospace" }}>
          {article.readTime}
        </span>
      </div>
      <h3 style={{ font: "600 15px 'Space Grotesk'", color: "var(--text-primary)", lineHeight: 1.4, margin: 0 }}>
        {article.title}
      </h3>
      <p style={{ fontSize: "12px", fontFamily: "'DM Sans', sans-serif", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0, flex: 1 }}>
        {article.excerpt}
      </p>
      <Link
        href={`/insights/${article.slug}`}
        style={{ fontFamily: "'DM Mono', monospace", fontSize: "10px", fontWeight: 700, color: "var(--accent-text)", textDecoration: "none", letterSpacing: "0.5px" }}
      >
        Read Article →
      </Link>
    </article>
  );
}
