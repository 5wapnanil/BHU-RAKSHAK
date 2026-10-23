"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import {
  LayoutDashboard,
  Stethoscope,
  Car,
  HeartHandshake,
  PersonStanding,
  ClipboardList,
  Package,
  Home,
  Bell,
  History,
  LayoutGrid,
  Database,
  ArrowUpRight,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: any;
  exact?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: "BACKEND OVERVIEW",
    items: [
      {
        href: "/app-backend",
        label: "Coordination Overview",
        icon: LayoutDashboard,
        exact: true,
      },
    ],
  },
  {
    title: "DISASTER COORDINATION",
    items: [
      {
        href: "/app-backend/requests/relief",
        label: "Relief Requests",
        icon: Stethoscope,
      },
      {
        href: "/app-backend/requests/evacuation",
        label: "Evacuation Requests",
        icon: Car,
      },
      {
        href: "/app-backend/volunteers/relief",
        label: "Relief Volunteers",
        icon: HeartHandshake,
      },
      {
        href: "/app-backend/volunteers/evacuation",
        label: "Evacuation Volunteers",
        icon: PersonStanding,
      },
      {
        href: "/app-backend/assignments",
        label: "Assignments",
        icon: ClipboardList,
      },
      {
        href: "/app-backend/resources",
        label: "Relief Resources",
        icon: Package,
      },
      {
        href: "/app-backend/shelters",
        label: "Shelters",
        icon: Home,
      },
      {
        href: "/app-backend/alerts",
        label: "Alerts",
        icon: Bell,
      },
      {
        href: "/app-backend/audit",
        label: "Audit / History",
        icon: History,
      },
    ],
  },
];

export default function AppBackendLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  function isActive(href: string, exact?: boolean) {
    if (exact) return pathname === href;
    return pathname === href || pathname.startsWith(href + "/");
  }

  return (
    <div className="analytics-layout" style={{ minHeight: "calc(100vh - 64px)" }}>
      {/* App Backend Operational Sidebar */}
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
        {/* Sidebar Brand Header */}
        <div style={{ padding: "0 0 16px", borderBottom: "1px solid var(--line)", marginBottom: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Database size={13} style={{ color: "var(--accent-text)" }} />
            <span style={{ font: "700 11px 'DM Mono'", letterSpacing: "1px", color: "var(--accent-text)", textTransform: "uppercase" }}>
              APP BACKEND
            </span>
          </div>
          <div style={{ font: "700 15px 'Space Grotesk'", color: "var(--text-primary)", marginTop: "2px" }}>
            Disaster Operations
          </div>
          <div style={{ font: "400 11px 'DM Sans'", color: "var(--text-secondary)", marginTop: "4px" }}>
            Live coordination &amp; field logistics
          </div>
        </div>

        {/* Navigation Sections */}
        {NAV_SECTIONS.map((section, idx) => (
          <div key={section.title} style={{ marginBottom: idx < NAV_SECTIONS.length - 1 ? "16px" : "8px" }}>
            <div
              className="analytics-sidebar-title"
              style={{
                color: "var(--text-secondary)",
                fontSize: "10px",
                letterSpacing: "1px",
                margin: "4px 0 8px 4px",
              }}
            >
              {section.title}
            </div>

            {section.items.map((item) => {
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
                    padding: "9px 12px",
                    borderRadius: "6px",
                    font: "600 12.5px 'DM Sans'",
                    textDecoration: "none",
                    marginBottom: "3px",
                  }}
                >
                  <item.icon size={15} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        ))}

        {/* Cross-Workspace Jump Links */}
        <div
          style={{
            marginTop: "auto",
            paddingTop: "16px",
            borderTop: "1px solid var(--line)",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          <Link
            href="/dashboard"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "8px 12px",
              borderRadius: "4px",
              backgroundColor: "rgba(142, 58, 26, 0.06)",
              border: "1px solid rgba(142, 58, 26, 0.2)",
              color: "var(--accent-text)",
              textDecoration: "none",
              font: "600 11.5px 'DM Sans'",
            }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <LayoutGrid size={13} />
              <span>Admin Panel</span>
            </span>
            <ArrowUpRight size={13} />
          </Link>

          <Link
            href="/"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "8px 12px",
              borderRadius: "4px",
              backgroundColor: "transparent",
              border: "1px solid var(--line)",
              color: "var(--text-secondary)",
              textDecoration: "none",
              font: "600 11.5px 'DM Sans'",
            }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Home size={13} />
              <span>Public Homepage</span>
            </span>
            <ArrowUpRight size={13} />
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
