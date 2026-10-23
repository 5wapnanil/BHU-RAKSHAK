"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import {
  LayoutDashboard,
  ClipboardList,
  MapPin,
  PlusCircle,
  Home,
  ShieldCheck,
  Mountain,
  Database,
} from "lucide-react";

const ADMIN_NAV_ITEMS = [
  {
    href: "/dashboard",
    label: "Overview",
    icon: LayoutDashboard,
    exact: true,
  },
  {
    href: "/dashboard/reports",
    label: "Field Reports",
    icon: ClipboardList,
  },
  {
    href: "/dashboard/map",
    label: "Observation Map",
    icon: MapPin,
  },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  function isActive(href: string, exact?: boolean) {
    if (exact) return pathname === href;
    return pathname.startsWith(href);
  }

  return (
    <div className="analytics-layout" style={{ minHeight: "calc(100vh - 64px)" }}>
      {/* Unified Administration Sidebar */}
      <aside
        className="analytics-sidebar"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "4px",
          borderRight: "1px solid var(--line)",
          backgroundColor: "var(--surface)",
        }}
      >
        <div style={{ padding: "0 0 16px", borderBottom: "1px solid var(--line)", marginBottom: "16px" }}>
          <div style={{ font: "700 11px 'DM Mono'", letterSpacing: "1px", color: "var(--accent-text)", textTransform: "uppercase" }}>
            ADMINISTRATION
          </div>
          <div style={{ font: "700 15px 'Space Grotesk'", color: "var(--text-primary)", marginTop: "2px" }}>
            Field Intelligence
          </div>
          <div style={{ font: "400 11px 'DM Sans'", color: "var(--text-secondary)", marginTop: "4px" }}>
            Ground observation &amp; review console
          </div>
        </div>

        <div className="analytics-sidebar-title" style={{ color: "var(--text-secondary)", fontSize: "10px", letterSpacing: "1px" }}>
          WORKSPACE
        </div>

        {ADMIN_NAV_ITEMS.map((item) => {
          const active = isActive(item.href, item.exact);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn("analytics-sidebar-btn", active && "active")}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "10px 14px",
                borderRadius: "6px",
                font: "600 13px 'DM Sans'",
                textDecoration: "none",
                marginBottom: "4px",
              }}
            >
              <item.icon size={16} />
              <span>{item.label}</span>
            </Link>
          );
        })}

        {/* Action Shortcuts & Public Links */}
        <div style={{ marginTop: "auto", paddingTop: "20px", borderTop: "1px solid var(--line)", display: "flex", flexDirection: "column", gap: "10px" }}>
          <Link
            href="/report"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              padding: "10px 12px",
              borderRadius: "4px",
              backgroundColor: "rgba(224, 90, 58, 0.1)",
              border: "1px solid rgba(224, 90, 58, 0.3)",
              color: "var(--accent-text)",
              textDecoration: "none",
              font: "700 11px 'DM Mono'",
              letterSpacing: "0.5px",
            }}
          >
            <PlusCircle size={14} />
            <span>SUBMIT FIELD REPORT</span>
          </Link>

          <Link
            href="/app-backend"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              padding: "8px 12px",
              borderRadius: "4px",
              backgroundColor: "rgba(142, 58, 26, 0.06)",
              border: "1px solid rgba(142, 58, 26, 0.2)",
              color: "var(--accent-text)",
              textDecoration: "none",
              font: "600 11px 'DM Sans'",
            }}
          >
            <Database size={13} />
            <span>App Backend Console</span>
          </Link>

          <Link
            href="/"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              padding: "8px 12px",
              borderRadius: "4px",
              backgroundColor: "transparent",
              border: "1px solid var(--line)",
              color: "var(--text-secondary)",
              textDecoration: "none",
              font: "600 11px 'DM Sans'",
            }}
          >
            <Home size={13} />
            <span>Public Homepage</span>
          </Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="analytics-main" style={{ flex: 1, padding: "28px" }}>
        {children}
      </main>
    </div>
  );
}
