import { FieldReport, ReviewStatus, HazardLevel, AIScreeningStatus } from "@/types/fieldReport";
import { apiFetch, API_URL, getApiBaseUrl } from "./api";

export function mapBackendRequestToFieldReport(req: any): FieldReport {
  const payload = req?.payload || {};

  // Resolve latitude & longitude
  let lat: number | null = null;
  let lng: number | null = null;

  if (typeof payload.latitude === "number" && !isNaN(payload.latitude)) {
    lat = payload.latitude;
  } else if (typeof req?.latitude === "number" && !isNaN(req.latitude)) {
    lat = req.latitude;
  } else if (payload.gpsCoords?.latitude && !isNaN(Number(payload.gpsCoords.latitude))) {
    lat = Number(payload.gpsCoords.latitude);
  } else if (Array.isArray(payload.gps_coords) && payload.gps_coords.length === 2) {
    lat = Number(payload.gps_coords[0]);
    lng = Number(payload.gps_coords[1]);
  }

  if (lng === null) {
    if (typeof payload.longitude === "number" && !isNaN(payload.longitude)) {
      lng = payload.longitude;
    } else if (typeof req?.longitude === "number" && !isNaN(req.longitude)) {
      lng = req.longitude;
    } else if (payload.gpsCoords?.longitude && !isNaN(Number(payload.gpsCoords.longitude))) {
      lng = Number(payload.gpsCoords.longitude);
    }
  }

  // Resolve review status
  let reviewStatus: ReviewStatus = "pending";
  const rawStatus = (req?.review_status || req?.status || "").toLowerCase();
  if (rawStatus === "verified" || rawStatus === "resolved") {
    reviewStatus = "verified";
  } else if (rawStatus === "under_review" || rawStatus === "in_progress") {
    reviewStatus = "under_review";
  } else if (rawStatus === "rejected") {
    reviewStatus = "rejected";
  } else if (rawStatus === "needs_inspection") {
    reviewStatus = "needs_inspection";
  } else {
    reviewStatus = "pending";
  }

  // Resolve hazard level from AI screening or severity
  let hazardLevel: HazardLevel = "indeterminate";
  const rawSeverity = (req?.ai_hazard_level || req?.severity || payload.severity || "").toLowerCase();
  if (rawSeverity === "critical") hazardLevel = "critical";
  else if (rawSeverity === "high") hazardLevel = "high";
  else if (rawSeverity === "moderate" || rawSeverity === "medium") hazardLevel = "moderate";
  else if (rawSeverity === "low") hazardLevel = "low";

  // Resolve observation notes
  const notes =
    req?.notes ||
    payload.description ||
    payload.notes ||
    req?.location_name ||
    "Field observation recorded without supplementary notes.";

  // Resolve location title
  const locationName =
    req?.location_name ||
    payload.location ||
    (lat !== null && lng !== null ? `Geotagged (${lat.toFixed(4)}, ${lng.toFixed(4)})` : "Unspecified Mountain Sector");

  const title = req?.title || payload.title || `Field Report: ${locationName}`;

  return {
    id: req?.id || "unknown",
    client_op_id: req?.client_op_id || null,
    title,
    notes,
    location_name: locationName,
    latitude: lat,
    longitude: lng,
    photo_url: (() => {
      let p = req?.photo_url || payload.photoUrl || payload.photo_url || null;
      if (!p) return null;
      if (typeof p === "string") {
        if (p.startsWith("http://") || p.startsWith("https://")) return p;
        const normalized = p.startsWith("/") ? p : `/${p}`;
        if (normalized.startsWith("/uploads")) {
          return `${getApiBaseUrl()}${normalized}`;
        }
      }
      return p;
    })(),
    thumbnail_url: req?.thumbnail_url || payload.thumbnailUrl || null,
    reporter_name: req?.reporter_name || payload.contactName || payload.name || "Field Scout",
    reporter_phone: req?.reporter_phone || payload.contactPhone || payload.phone || null,
    submitted_at: req?.submitted_at || req?.created_at || payload.submittedAt || new Date().toISOString(),

    // AI Preliminary Screening (Gemma Multimodal)
    ai_status: req?.ai_status || (req?.ai_analyzed_at ? "completed" : "pending"),
    ai_screening_status: req?.ai_status || (req?.ai_analyzed_at ? "completed" : "pending"),
    ai_hazard_level: hazardLevel,
    ai_confidence: typeof req?.ai_confidence === "number" ? req.ai_confidence : null,
    ai_detected_hazards: Array.isArray(req?.ai_detected_hazards) ? req.ai_detected_hazards : [],
    ai_summary: req?.ai_summary || null,
    ai_analyzed_at: req?.ai_analyzed_at || null,
    ai_disclaimer:
      "Preliminary AI screening is not certified geotechnical assessment. Geotechnical specialist verification required.",

    // Human Review
    review_status: reviewStatus,
    reviewed_at: req?.reviewed_at || req?.updated_at || null,
    reviewed_by: req?.reviewed_by || payload.reviewedBy || null,
    admin_notes: req?.admin_notes || payload.adminNotes || null,
    linked_incident_id: req?.linked_incident_id || null,
  };
}

/**
 * Query the status of the dedicated `/api/field-reports` endpoint.
 * Detects whether the endpoint is implemented on the backend.
 */
export async function getFieldReportsStatus(): Promise<{ isReady: boolean; reports: FieldReport[] }> {
  try {
    const rawList = await apiFetch<any>("/api/field-reports?limit=100");
    const items = Array.isArray(rawList) ? rawList : (Array.isArray(rawList?.items) ? rawList.items : []);
    return { isReady: true, reports: items.map(mapBackendRequestToFieldReport) };
  } catch {
    return { isReady: false, reports: [] };
  }
}

/**
 * Fetch dedicated field reports from the backend.
 */
export async function fetchFieldReports(statusFilter?: string): Promise<FieldReport[]> {
  try {
    const url = statusFilter && statusFilter !== 'all'
      ? `/api/field-reports?review_status=${encodeURIComponent(statusFilter === 'under_review' ? 'needs_inspection' : statusFilter)}&limit=100`
      : `/api/field-reports?limit=100`;
    const resp = await apiFetch<any>(url);
    const items = Array.isArray(resp) ? resp : (Array.isArray(resp?.items) ? resp.items : []);
    return items.map(mapBackendRequestToFieldReport);
  } catch {
    return [];
  }
}

export async function fetchFieldReportById(id: string): Promise<FieldReport | null> {
  try {
    const raw = await apiFetch<any>(`/api/field-reports/${id}`);
    if (!raw || !raw.id) return null;
    return mapBackendRequestToFieldReport(raw);
  } catch {
    return null;
  }
}

export async function submitFieldReportDirectly(
  data: FormData | {
    notes?: string;
    location_name?: string;
    latitude?: number | null;
    longitude?: number | null;
    reporter_name?: string;
    reporter_phone?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const baseUrl = getApiBaseUrl();
    const isFormData = typeof FormData !== "undefined" && data instanceof FormData;
    const res = await fetch(`${baseUrl}/api/field-reports`, {
      method: "POST",
      headers: isFormData ? {} : { "Content-Type": "application/json" },
      body: isFormData ? data : JSON.stringify(data),
    });

    if (!res.ok) {
      let errBody;
      try {
        errBody = await res.json();
      } catch {
        errBody = { detail: res.statusText };
      }
      return {
        success: false,
        error: errBody?.detail || `Server rejected submission (HTTP ${res.status})`,
      };
    }

    const json = await res.json();
    return { success: true, data: json };
  } catch (err: any) {
    return { success: false, error: err?.message || "Network connection failure" };
  }
}

export async function updateFieldReportStatus(
  id: string,
  newStatus: ReviewStatus,
  adminNotes?: string
): Promise<{ success: boolean; error?: string }> {
  try {
    const backendStatus = newStatus === "under_review" ? "needs_inspection" : newStatus;
    const isBrowser = typeof window !== "undefined";
    const targetUrl = isBrowser
      ? `/api/field-reports/${id}/review`
      : `${getApiBaseUrl()}/api/field-reports/${id}/review`;

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    // Server-only coordinator authorization (never read or bundled in browser)
    if (!isBrowser && process.env.COORDINATOR_API_KEY) {
      headers["X-Coordinator-Key"] = process.env.COORDINATOR_API_KEY;
    }

    const res = await fetch(targetUrl, {
      method: "PATCH",
      headers,
      body: JSON.stringify({
        review_status: backendStatus,
        admin_notes: adminNotes || null,
      }),
    });

    if (res.ok) {
      return { success: true };
    } else {
      let errJson;
      try {
        errJson = await res.json();
      } catch {
        errJson = {};
      }
      return {
        success: false,
        error: errJson?.detail || `Server responded with HTTP ${res.status}`,
      };
    }
  } catch (err: any) {
    return { success: false, error: err.message || "Network error" };
  }
}

/**
 * Trigger or retry Gemma AI hazard screening for a field report.
 */
export async function triggerFieldReportAnalysis(
  id: string,
  force: boolean = false
): Promise<{ success: boolean; data?: FieldReport; error?: string }> {
  try {
    const isBrowser = typeof window !== "undefined";
    const targetUrl = isBrowser
      ? `/api/field-reports/${id}/analyze${force ? "?force=true" : ""}`
      : `${getApiBaseUrl()}/api/field-reports/${id}/analyze${force ? "?force=true" : ""}`;

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    // Server-only coordinator authorization (never read or bundled in browser)
    if (!isBrowser && process.env.COORDINATOR_API_KEY) {
      headers["X-Coordinator-Key"] = process.env.COORDINATOR_API_KEY;
    }

    const res = await fetch(targetUrl, {
      method: "POST",
      headers,
    });

    if (!res.ok) {
      let errJson;
      try {
        errJson = await res.json();
      } catch {
        errJson = {};
      }
      return {
        success: false,
        error: errJson?.detail || `AI analysis failed (HTTP ${res.status})`,
      };
    }

    const data = await res.json();
    return { success: true, data: mapBackendRequestToFieldReport(data) };
  } catch (err: any) {
    return { success: false, error: err?.message || "Network error triggering AI analysis" };
  }
}

/**
 * Fetch detailed AI screening metadata and reasoning for a field report.
 */
export async function fetchFieldReportAIAnalysis(
  id: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const baseUrl = getApiBaseUrl();
    const res = await fetch(`${baseUrl}/api/field-reports/${id}/ai-analysis`);
    if (!res.ok) {
      return { success: false, error: `Could not retrieve AI analysis (HTTP ${res.status})` };
    }
    const data = await res.json();
    return { success: true, data };
  } catch (err: any) {
    return { success: false, error: err?.message || "Network error fetching AI analysis" };
  }
}
