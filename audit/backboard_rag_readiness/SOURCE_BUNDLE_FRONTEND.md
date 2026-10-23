# PahaarPulse — Sanitized Frontend & Mobile Source Bundle for Backboard RAG Integration

This document contains key frontend (Next.js) and mobile (React Native/Expo) architectural files illustrating dependency versions, API clients, Backend-For-Frontend (BFF) proxy routes, navigation, and candidate knowledge bases.

---

## 1. Web Frontend Manifest: `frontend/package.json`

```json
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint"
  },
  "dependencies": {
    "@types/leaflet": "^1.9.22",
    "@types/leaflet.heat": "^0.2.5",
    "@types/leaflet.markercluster": "^1.5.6",
    "clsx": "^2.1.1",
    "framer-motion": "^13.2.0",
    "gsap": "^3.15.0",
    "idb": "^8.0.3",
    "leaflet": "^1.9.4",
    "leaflet.heat": "^0.2.0",
    "leaflet.markercluster": "^1.5.3",
    "lucide-react": "^1.41.0",
    "next": "16.3.4",
    "react": "19.2.8",
    "react-dom": "19.2.8",
    "react-hot-toast": "^2.6.0",
    "react-leaflet": "^5.0.0",
    "react-leaflet-cluster": "^4.1.3",
    "recharts": "^3.10.1",
    "tailwind-merge": "^3.6.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.3.4",
    "tailwindcss": "^4",
    "typescript": "^5"
  }
}
```

---

## 2. Web API Client: `frontend/src/lib/api.ts`

```typescript
/**
 * Dynamic API base URL resolution.
 * - Respects NEXT_PUBLIC_API_URL if configured with an explicit external host or protocol.
 * - In browser environments (desktop, mobile LAN, Android emulator), automatically aligns
 *   with window.location.hostname on port 8000 (or NEXT_PUBLIC_API_PORT).
 * - Falls back to http://localhost:8000 for SSR and local environments.
 */
export function getApiBaseUrl(): string {
  if (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL) {
    const configured = process.env.NEXT_PUBLIC_API_URL;
    if (!configured.includes("localhost") && !configured.includes("127.0.0.1")) {
      return configured.replace(/\/+$/, "");
    }
  }
  if (typeof window !== "undefined" && window.location?.hostname) {
    const port = (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_PORT) || "8000";
    return `http://${window.location.hostname}:${port}`;
  }
  return (typeof process !== "undefined" && process.env?.NEXT_PUBLIC_API_URL) || "http://localhost:8000";
}

const API_URL = getApiBaseUrl();
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_DATA === "true";

export { API_URL, USE_MOCK };

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const res = await fetch(`${baseUrl}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  return apiFetch<T>(path, { method: "POST", body: JSON.stringify(body) });
}
```

---

## 3. Next.js App Router BFF Proxy Route: `frontend/src/app/api/field-reports/[id]/review/route.ts`

```typescript
import { NextResponse } from "next/server";

function getBackendBaseUrl(): string {
  return (
    process.env.BACKEND_INTERNAL_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
}

function validateOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host") || request.headers.get("x-forwarded-host");
  
  if (origin) {
    try {
      const originUrl = new URL(origin);
      if (!host) return false;
      const hostName = host.split(":")[0];
      return originUrl.hostname === hostName || originUrl.host === host;
    } catch {
      return false;
    }
  }

  const secFetchSite = request.headers.get("sec-fetch-site");
  if (secFetchSite && (secFetchSite === "cross-site" || secFetchSite === "none")) {
    return false;
  }

  return true;
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  // 1. Cross-Origin / CSRF Protection
  if (!validateOrigin(request)) {
    return NextResponse.json(
      { detail: "Forbidden: Cross-origin request rejected." },
      { status: 403 }
    );
  }

  const { id } = await params;
  if (!id) {
    return NextResponse.json({ detail: "Missing report ID." }, { status: 400 });
  }

  const envName = (
    process.env.ENVIRONMENT ||
    process.env.APP_ENV ||
    process.env.FASTAPI_ENV ||
    process.env.NODE_ENV ||
    process.env.ENV ||
    ""
  ).toLowerCase().trim();
  const isProduction = ["production", "prod", "live", "staging"].includes(envName);

  // 2. Authentication & Authorization Enforcement
  const incomingCoordKey = request.headers.get("x-coordinator-key");
  const incomingAuthHeader = request.headers.get("authorization");
  const serverCoordKey = (process.env.COORDINATOR_API_KEY || "").trim();

  if (isProduction && !serverCoordKey && !incomingCoordKey && !incomingAuthHeader) {
    return NextResponse.json(
      { detail: "Authentication required: Coordinator credentials are not configured." },
      { status: 503 }
    );
  }

  // 3. Prepare headers for upstream backend request
  const upstreamHeaders: Record<string, string> = { "Content-Type": "application/json" };
  if (incomingCoordKey) {
    upstreamHeaders["X-Coordinator-Key"] = incomingCoordKey;
  } else if (incomingAuthHeader) {
    upstreamHeaders["Authorization"] = incomingAuthHeader;
  } else if (!isProduction && serverCoordKey) {
    upstreamHeaders["X-Coordinator-Key"] = serverCoordKey;
  }

  let bodyText = "";
  try {
    bodyText = await request.text();
  } catch {
    bodyText = "{}";
  }

  const backendUrl = `${getBackendBaseUrl()}/api/field-reports/${id}/review`;

  try {
    const upstreamRes = await fetch(backendUrl, {
      method: "PATCH",
      headers: upstreamHeaders,
      body: bodyText,
    });

    const responseContentType = upstreamRes.headers.get("content-type") || "";
    let data;
    if (responseContentType.includes("application/json")) {
      data = await upstreamRes.json();
    } else {
      data = { detail: await upstreamRes.text() };
    }

    return NextResponse.json(data, { status: upstreamRes.status });
  } catch (err: any) {
    return NextResponse.json(
      { detail: "Backend communication error: Unable to contact central API server." },
      { status: 502 }
    );
  }
}
```

---

## 4. Dashboard Layout & Navigation: `frontend/src/app/dashboard/layout.tsx`

```typescript
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
  // Future Backboard RAG Assistant navigation item can be inserted here
];
```

---

## 5. Domain Knowledge Corpus: `frontend/src/data/articles.ts` (Sample)

```typescript
export interface ArticleSection {
  heading: string;
  content: string[];
}

export interface Article {
  id: string;
  slug: string;
  category: string;
  title: string;
  excerpt: string;
  readTime: string;
  featured: boolean;
  publishedAt: string;
  author: string;
  content: ArticleSection[];
}

export const ARTICLES: Article[] = [
  {
    id: "1",
    slug: "why-do-landslides-happen",
    category: "LANDSLIDE SCIENCE",
    title: "Why Do Landslides Happen? Understanding the Signals Before Failure",
    excerpt: "Landslides are triggered by a combination of geological, environmental, and human factors. Understanding these signals is the first step toward risk assessment.",
    readTime: "6 min read",
    featured: true,
    publishedAt: "2026-08-15",
    author: "LRM Research Team",
    content: [
      {
        heading: "What Causes Landslides?",
        content: [
          "Landslides occur when the forces driving slope movement exceed the forces resisting it...",
          "Slope instability is influenced by gravity, the internal strength of soil and rock, and terrain geometry..."
        ]
      },
      {
        heading: "The Role of Rainfall and Soil Moisture",
        content: [
          "Rainfall is one of the most common triggers of landslides...",
          "Cumulative rainfall over several days can saturate soil layers gradually..."
        ]
      }
    ]
  }
  // Total 6 structured articles: GIS Risk Mapping, ML Prediction, Rainfall & Soil Moisture, Satellite Monitoring, Early Warning
];
```

---

## 6. Mobile Application Configuration: `landslide-app/src/services/api/apiConfig.ts`

```typescript
import { Platform } from 'react-native';

const EMULATOR_BASE_URL = 'http://10.0.2.2:8000';
const LAN_BASE_URL = 'http://192.168.0.102:8000';

function isAndroidEmulator(): boolean {
  if (Platform.OS !== 'android') return false;
  const androidConstants = Platform.constants as Record<string, unknown>;
  const model = String(androidConstants.Model ?? '');
  const fingerprint = String(androidConstants.Fingerprint ?? '');
  return /sdk|emulator|generic|genymotion|vbox/i.test(model + fingerprint);
}

function getDevBaseUrl(): string {
  if (Platform.OS === 'web') {
    if (typeof window !== 'undefined' && window.location?.hostname) {
      return `http://${window.location.hostname}:8000`;
    }
    return 'http://localhost:8000';
  }
  if (Platform.OS !== 'android') return LAN_BASE_URL;
  return isAndroidEmulator() ? EMULATOR_BASE_URL : LAN_BASE_URL;
}

export const API_CONFIG = {
  baseUrl: __DEV__ ? getDevBaseUrl() : '',
  timeout: 30000,
  endpoints: {
    health: '/health',
    prediction: {
      base: '/prediction',
      location: '/prediction/location',
      custom: '/prediction/custom',
    },
    environment: '/environmental-data/location',
    alerts: {
      base: '/api/alerts',
      ws: '/api/alerts/ws',
    },
    riskZones: {
      base: '/api/risk-zones',
      nerRiskData: '/api/risk-zones/ner-risk-data',
      nearby: '/api/risk-zones/nearby',
    },
    sync: '/api/sync/upload',
    gis: '/api/gis/road-impact/analyze',
    analytics: '/analytics/historical',
    assignments: '/api/assignments',
    reliefResources: '/api/relief-resources',
    shelters: '/api/shelters',
    fieldReports: '/api/field-reports',
    // Candidate: assistant: '/api/assistant/query'
  },
};
```
