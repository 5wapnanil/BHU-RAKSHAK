"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Mountain, FileText, LayoutGrid, Home, Database, Menu, X, Sparkles } from "lucide-react";

const NAV_LINKS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/assistant", label: "AI Assistant", icon: Sparkles },
  { href: "/report", label: "Field Report", icon: FileText },
  { href: "/dashboard", label: "Admin Panel", icon: LayoutGrid },
  { href: "/app-backend", label: "App Backend", icon: Database },
];

export default function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <header
      className="topbar"
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        backgroundColor: "rgba(245, 238, 230, 0.94)",
        backdropFilter: "blur(12px)",
        WebkitBackdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(224, 214, 202, 0.8)",
        height: "64px",
      }}
    >
      {/* Brand Identity */}
      <div className="brand-mark">
        <Link
          href="/"
          className="flex items-center gap-3 no-underline"
          onClick={() => setMobileMenuOpen(false)}
        >
          {/* Mountain Box Logo */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              background: "#FAF4EC",
              border: "1px solid #D6CCC8",
              boxShadow: "0 2px 5px rgba(0, 0, 0, 0.04)",
            }}
          >
            <Mountain className="h-5 w-5" style={{ color: "#8E3A1A" }} strokeWidth={2.2} />
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <span
              style={{
                font: "700 18px 'Space Grotesk', sans-serif",
                letterSpacing: "-0.5px",
                color: "#231F20",
                lineHeight: 1.15,
              }}
            >
              PahaarPulse
            </span>
            <span
              style={{
                font: "700 9px 'DM Mono', monospace",
                letterSpacing: "1px",
                color: "#8E3A1A",
                textTransform: "uppercase",
              }}
            >
              FIELD INTELLIGENCE
            </span>
          </div>
        </Link>
      </div>

      {/* Desktop Navigation - Exactly Three Destinations */}
      <nav className="hidden md:flex items-center gap-4">
        {NAV_LINKS.map((link) => {
          const active = isActive(link.href);
          const Icon = link.icon;
          return (
            <Link
              key={link.href}
              href={link.href}
              className="relative flex items-center gap-2 px-3 py-2 text-sm no-underline transition-colors"
              style={{
                fontFamily: "'DM Sans', sans-serif",
                fontWeight: active ? 600 : 500,
                color: active ? "#231F20" : "#736B63",
              }}
            >
              <Icon
                className="h-4 w-4"
                style={{ color: active ? "#8E3A1A" : "#8A8178" }}
              />
              <span>{link.label}</span>

              {/* Active Underline Indicator matching reference */}
              {active && (
                <span
                  style={{
                    position: "absolute",
                    bottom: "-12px",
                    left: "12px",
                    right: "12px",
                    height: "2.5px",
                    backgroundColor: "#8E3A1A",
                    borderRadius: "2px",
                  }}
                />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Mobile Hamburger Button */}
      <div className="flex md:hidden items-center">
        <button
          type="button"
          aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          style={{
            background: "transparent",
            border: "1px solid #D6CCC8",
            borderRadius: "6px",
            padding: "8px",
            cursor: "pointer",
            color: "#231F20",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile Dropdown Menu */}
      {mobileMenuOpen && (
        <div
          style={{
            position: "absolute",
            top: "64px",
            left: 0,
            right: 0,
            background: "#FAF4EC",
            borderBottom: "1px solid #D6CCC8",
            padding: "16px 5vw",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            boxShadow: "0 10px 25px -5px rgba(0,0,0,0.1)",
            zIndex: 100,
          }}
          className="md:hidden"
        >
          {NAV_LINKS.map((link) => {
            const active = isActive(link.href);
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 rounded text-sm no-underline"
                style={{
                  fontFamily: "'DM Sans', sans-serif",
                  fontWeight: active ? 700 : 500,
                  color: active ? "#8E3A1A" : "#231F20",
                  backgroundColor: active ? "rgba(142, 58, 26, 0.08)" : "transparent",
                  borderLeft: active ? "3px solid #8E3A1A" : "3px solid transparent",
                }}
              >
                <Icon className="h-4 w-4" style={{ color: active ? "#8E3A1A" : "#736B63" }} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </div>
      )}
    </header>
  );
}
