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
  
  // If browser sent an explicit Origin header, enforce same-host check
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

  // Cross-site fetch protection via Fetch Metadata if present
  const secFetchSite = request.headers.get("sec-fetch-site");
  if (secFetchSite && (secFetchSite === "cross-site" || secFetchSite === "none")) {
    return false;
  }

  return true;
}

export async function POST(
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

  // In production deployments:
  // - If server credentials are not configured at all: FAIL CLOSED (503)
  if (isProduction && !serverCoordKey && !incomingCoordKey && !incomingAuthHeader) {
    return NextResponse.json(
      {
        detail:
          "Authentication required: Coordinator credentials are not configured or provided for production deployment.",
      },
      { status: 503 }
    );
  }

  // - Confused deputy prevention: In production, the proxy NEVER signs on behalf of an anonymous caller.
  //   Caller must provide explicit coordinator credentials.
  if (isProduction && !incomingCoordKey && !incomingAuthHeader) {
    return NextResponse.json(
      {
        detail:
          "Authentication required: Coordinator credentials must be provided for privileged mutations.",
      },
      { status: 401 }
    );
  }

  // 3. Prepare headers for upstream backend request
  const upstreamHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (incomingCoordKey) {
    upstreamHeaders["X-Coordinator-Key"] = incomingCoordKey;
  } else if (incomingAuthHeader) {
    upstreamHeaders["Authorization"] = incomingAuthHeader;
  } else if (!isProduction && serverCoordKey) {
    // Development-only fallback: attach server key for local developer UI testing
    upstreamHeaders["X-Coordinator-Key"] = serverCoordKey;
  }

  const incomingUrl = new URL(request.url);
  const force = incomingUrl.searchParams.get("force") === "true";

  const backendUrl = `${getBackendBaseUrl()}/api/field-reports/${id}/analyze${
    force ? "?force=true" : ""
  }`;

  try {
    const upstreamRes = await fetch(backendUrl, {
      method: "POST",
      headers: upstreamHeaders,
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
