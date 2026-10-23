/**
 * BhuRakshak / PahaarPulse AI Assistant Web Client Module.
 *
 * Communicates with the FastAPI assistant backend:
 * - Session Initialization: POST /api/assistant/threads?transport=cookie
 * - Query Submission:     POST /api/assistant/query
 *
 * SECURITY & PRIVACY INVARIANTS:
 * 1. Web client relies exclusively on HttpOnly cookie transport ('pp_assistant_session').
 * 2. Never accesses, copies, or stores session tokens or credentials in JavaScript (localStorage/sessionStorage).
 * 3. Never sends client-controlled Backboard assistant_id or thread_id.
 * 4. Includes credentials='include' and same-origin / trusted-origin headers.
 * 5. Sanitizes and validates query strings before submission.
 */

import { getApiBaseUrl } from "./api";

export interface SourceCitation {
  title: string;
  document_id: string;
  url_or_slug?: string | null;
  category?: string | null;
  is_curated: boolean;
}

export interface AssistantQueryResponse {
  reply: string;
  sources: SourceCitation[];
  disclaimer: string;
  fallback_mode: boolean;
}

export interface AssistantThreadResponse {
  transport: "cookie" | "bearer";
  expires_at: string;
  session_token: string | null;
}

export interface AssistantChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  sources?: SourceCitation[];
  disclaimer?: string;
  fallbackMode?: boolean;
  timestamp: string;
  isError?: boolean;
}

export class AssistantApiError extends Error {
  statusCode: number;
  isRetryable: boolean;

  constructor(message: string, statusCode: number = 500, isRetryable: boolean = false) {
    super(message);
    this.name = "AssistantApiError";
    this.statusCode = statusCode;
    this.isRetryable = isRetryable;
  }
}

/**
 * Initialize an anonymous conversation thread session via HttpOnly cookie.
 * The backend sets the 'pp_assistant_session' cookie on path '/api/assistant'.
 */
export async function initWebAssistantSession(): Promise<AssistantThreadResponse> {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/assistant/threads?transport=cookie`;

  let res: Response;
  try {
    res = await fetch(endpoint, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Network error";
    throw new AssistantApiError(`Failed to connect to assistant service: ${message}`, 0, true);
  }

  if (!res.ok) {
    let errorDetail = "Failed to initialize conversation session.";
    try {
      const errJson = await res.json();
      if (errJson?.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Ignore JSON parse errors on non-200 responses
    }

    if (res.status === 429) {
      throw new AssistantApiError("Session initialization rate limit reached. Please wait a few minutes.", 429, false);
    }
    if (res.status === 504) {
      throw new AssistantApiError("AI knowledge service timed out during initialization. Please try again.", 504, true);
    }
    throw new AssistantApiError(`Session error (${res.status}): ${errorDetail}`, res.status, res.status >= 500);
  }

  const data: AssistantThreadResponse = await res.json();
  return data;
}

/**
 * Submit a domain query to the assistant.
 * If the session is uninitialized or expired (HTTP 401), automatically refreshes
 * the session once and retries the query.
 */
export async function sendAssistantQuery(
  query: string,
  retryOnAuthFailure: boolean = true
): Promise<AssistantQueryResponse> {
  const trimmed = query.trim();
  if (trimmed.length < 2) {
    throw new AssistantApiError("Query must be at least 2 characters long.", 422, false);
  }
  if (trimmed.length > 1000) {
    throw new AssistantApiError("Query exceeds maximum allowed length of 1,000 characters.", 422, false);
  }

  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/assistant/query`;

  let res: Response;
  try {
    res = await fetch(endpoint, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: trimmed }),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Network error";
    throw new AssistantApiError(`Failed to connect to assistant service: ${message}`, 0, true);
  }

  // Handle session expiration: reinitialize and retry once
  if (res.status === 401 && retryOnAuthFailure) {
    await initWebAssistantSession();
    return sendAssistantQuery(trimmed, false);
  }

  if (!res.ok) {
    let errorDetail = "Failed to process query.";
    try {
      const errJson = await res.json();
      if (errJson?.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Ignore JSON parse errors
    }

    if (res.status === 429) {
      throw new AssistantApiError(
        "Rate limit exceeded (maximum 10 queries per minute). Please pause before asking another question.",
        429,
        false
      );
    }
    if (res.status === 504) {
      throw new AssistantApiError(
        "AI knowledge service timed out generating a response. Please try asking a more focused question.",
        504,
        true
      );
    }
    if (res.status === 403) {
      throw new AssistantApiError(
        "Request rejected due to origin verification. Please ensure you are accessing via the official domain.",
        403,
        false
      );
    }
    throw new AssistantApiError(`Query error (${res.status}): ${errorDetail}`, res.status, res.status >= 500);
  }

  const data: AssistantQueryResponse = await res.json();
  return data;
}

export const SUGGESTED_QUESTIONS = [
  "Why do landslides happen and what early physical signals precede slope failure?",
  "How do rainfall intensity, duration, and soil moisture influence slope stability?",
  "How do GIS spatial layers and terrain factors combine to produce landslide susceptibility maps?",
  "How does machine learning predict landslide risk across the three-layer pipeline?",
  "How do landslide risk maps and sensor thresholds translate into operational early-warning decisions?",
] as const;
