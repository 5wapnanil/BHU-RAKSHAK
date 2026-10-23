"use client";

const shimmer = {
  background: "linear-gradient(90deg, var(--surface) 25%, var(--line) 50%, var(--surface) 75%)",
  backgroundSize: "200% 100%",
  animation: "shimmer 1.5s ease-in-out infinite",
  borderRadius: "3px",
};

export function Skeleton({ style }: { style?: React.CSSProperties }) {
  return <div style={{ ...shimmer, ...style }} />;
}

export function StatSkeleton() {
  return (
    <div style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)", borderRadius: "6px", padding: "20px 24px", flex: "1 1 200px", minWidth: 200 }}>
      <Skeleton style={{ width: "60%", height: 12, marginBottom: 12 }} />
      <Skeleton style={{ width: "40%", height: 28, marginBottom: 8 }} />
      <Skeleton style={{ width: "50%", height: 10 }} />
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="card" style={{ borderTop: "3px solid var(--line)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <Skeleton style={{ width: 60, height: 10 }} />
        <Skeleton style={{ width: 30, height: 10 }} />
      </div>
      <Skeleton style={{ width: "80%", height: 16, marginBottom: 10 }} />
      <Skeleton style={{ width: "100%", height: 10, marginBottom: 6 }} />
      <Skeleton style={{ width: "90%", height: 10, marginBottom: 6 }} />
      <Skeleton style={{ width: "40%", height: 10, marginTop: 12 }} />
    </div>
  );
}

export function ArticleCardSkeleton() {
  return (
    <div className="card" style={{ borderTop: "3px solid var(--line)", display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <Skeleton style={{ width: 100, height: 10 }} />
        <Skeleton style={{ width: 60, height: 10 }} />
      </div>
      <Skeleton style={{ width: "90%", height: 16 }} />
      <Skeleton style={{ width: "100%", height: 10 }} />
      <Skeleton style={{ width: "80%", height: 10 }} />
      <Skeleton style={{ width: "30%", height: 10, marginTop: 4 }} />
    </div>
  );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div style={{ display: "grid", gap: 8 }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ display: "flex", gap: 16, padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
          <Skeleton style={{ width: "20%", height: 12 }} />
          <Skeleton style={{ width: "15%", height: 12 }} />
          <Skeleton style={{ width: "15%", height: 12 }} />
          <Skeleton style={{ width: "10%", height: 12 }} />
        </div>
      ))}
    </div>
  );
}

export function MapSkeleton() {
  return (
    <div style={{ height: 480, width: "100%", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--surface)", border: "1px solid var(--card-border)" }}>
      <div style={{ textAlign: "center" }}>
        <Skeleton style={{ width: 200, height: 200, borderRadius: "50%", margin: "0 auto 16px" }} />
        <Skeleton style={{ width: 120, height: 12, margin: "0 auto" }} />
      </div>
    </div>
  );
}

export function PredictionSkeleton() {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
      <div className="card">
        <Skeleton style={{ width: "50%", height: 12, marginBottom: 20 }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 16 }}>
          <Skeleton style={{ height: 36 }} />
          <Skeleton style={{ height: 36 }} />
        </div>
        <Skeleton style={{ height: 1, marginBottom: 16 }} />
        <Skeleton style={{ width: "40%", height: 10, marginBottom: 14 }} />
        <Skeleton style={{ height: 36, marginBottom: 14 }} />
        <Skeleton style={{ height: 36, marginBottom: 14 }} />
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <Skeleton style={{ height: 36 }} />
          <Skeleton style={{ height: 36 }} />
        </div>
      </div>
      <div style={{ display: "grid", gap: 16 }}>
        <div className="card" style={{ textAlign: "center", padding: 32 }}>
          <Skeleton style={{ width: "40%", height: 10, margin: "0 auto 12px" }} />
          <Skeleton style={{ width: 80, height: 30, margin: "0 auto 12px" }} />
          <Skeleton style={{ width: "50%", height: 40, margin: "0 auto 8px" }} />
          <Skeleton style={{ width: "30%", height: 10, margin: "0 auto" }} />
        </div>
        <div className="card">
          <Skeleton style={{ width: "40%", height: 12, marginBottom: 16 }} />
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} style={{ height: 32, marginBottom: 8 }} />
          ))}
        </div>
      </div>
    </div>
  );
}

export function ArticleDetailSkeleton() {
  return (
    <div>
      <Skeleton style={{ width: 100, height: 10, marginBottom: 24 }} />
      <Skeleton style={{ width: "60%", height: 12, marginBottom: 12 }} />
      <Skeleton style={{ width: "90%", height: 28, marginBottom: 16 }} />
      <div style={{ display: "flex", gap: 16, marginBottom: 32 }}>
        <Skeleton style={{ width: 80, height: 10 }} />
        <Skeleton style={{ width: 60, height: 10 }} />
        <Skeleton style={{ width: 80, height: 10 }} />
      </div>
      <Skeleton style={{ height: 1, marginBottom: 32 }} />
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} style={{ marginBottom: 32 }}>
          <Skeleton style={{ width: "40%", height: 18, marginBottom: 12 }} />
          <Skeleton style={{ width: "100%", height: 12, marginBottom: 8 }} />
          <Skeleton style={{ width: "95%", height: 12, marginBottom: 8 }} />
          <Skeleton style={{ width: "90%", height: 12 }} />
        </div>
      ))}
    </div>
  );
}
