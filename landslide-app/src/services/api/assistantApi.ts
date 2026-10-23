/**
 * BhuRakshak / PahaarPulse Mobile AI Assistant API Client.
 *
 * Implements the mobile client contract:
 * - Session Initialization: POST /api/assistant/threads?transport=bearer
 * - Query Submission:     POST /api/assistant/query
 *
 * SECURITY & STORAGE INVARIANTS:
 * 1. Bearer session tokens are stored ONLY in-memory during the active app lifecycle.
 *    No sensitive session material is written to persistent AsyncStorage or logs.
 * 2. Backboard API keys and backend signing keys are NEVER bundled or referenced in the mobile app.
 * 3. Client never supplies or overrides thread_id or assistant_id.
 * 4. Transparently handles session expiry (HTTP 401) by re-initializing and retrying once.
 */

import { API_CONFIG } from './apiConfig';

export interface MobileSourceCitation {
  title: string;
  document_id: string;
  url_or_slug?: string | null;
  category?: string | null;
  is_curated: boolean;
}

export interface MobileAssistantResponse {
  reply: string;
  sources: MobileSourceCitation[];
  disclaimer: string;
  fallback_mode: boolean;
}

export interface MobileAssistantMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  sources?: MobileSourceCitation[];
  disclaimer?: string;
  fallbackMode?: boolean;
  timestamp: string;
  isError?: boolean;
}

export class MobileAssistantError extends Error {
  statusCode: number;
  isRetryable: boolean;

  constructor(message: string, statusCode: number = 500, isRetryable: boolean = false) {
    super(message);
    this.name = 'MobileAssistantError';
    this.statusCode = statusCode;
    this.isRetryable = isRetryable;
  }
}

class MobileAssistantService {
  private sessionToken: string | null = null;
  private tokenExpiresAt: string | null = null;

  /**
   * Reset in-memory session token.
   */
  public resetSession(): void {
    this.sessionToken = null;
    this.tokenExpiresAt = null;
  }

  /**
   * Initialize a new conversation thread session and obtain a signed bearer token.
   */
  public async initSession(): Promise<string> {
    const baseUrl = API_CONFIG.baseUrl;
    const url = `${baseUrl}${API_CONFIG.endpoints.assistant.threads}?transport=bearer`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Network failure';
      throw new MobileAssistantError(`Failed to connect to assistant: ${msg}`, 0, true);
    }

    if (!response.ok) {
      let detail = 'Session initialization failed';
      try {
        const body = await response.json();
        if (body?.detail) {
          detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
        }
      } catch {
        // Ignore parse error
      }

      if (response.status === 429) {
        throw new MobileAssistantError('Session rate limit reached. Please wait before retrying.', 429, false);
      }
      if (response.status === 504) {
        throw new MobileAssistantError('Assistant service timed out during startup. Please retry.', 504, true);
      }
      throw new MobileAssistantError(`Session error (${response.status}): ${detail}`, response.status, response.status >= 500);
    }

    const data = await response.json();
    if (!data.session_token) {
      throw new MobileAssistantError('Server did not return a session token.', 500, false);
    }

    this.sessionToken = data.session_token;
    this.tokenExpiresAt = data.expires_at || null;
    return this.sessionToken as string;
  }

  /**
   * Submit a question to the assistant with bearer token authorization.
   */
  public async query(queryText: string, retryOnAuthFailure: boolean = true): Promise<MobileAssistantResponse> {
    const trimmed = queryText.trim();
    if (trimmed.length < 2) {
      throw new MobileAssistantError('Question must be at least 2 characters long.', 422, false);
    }
    if (trimmed.length > 1000) {
      throw new MobileAssistantError('Question cannot exceed 1,000 characters.', 422, false);
    }

    if (!this.sessionToken) {
      await this.initSession();
    }

    const baseUrl = API_CONFIG.baseUrl;
    const url = `${baseUrl}${API_CONFIG.endpoints.assistant.query}`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.sessionToken}`,
        },
        body: JSON.stringify({ query: trimmed }),
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Network failure';
      throw new MobileAssistantError(`Unable to reach assistant: ${msg}`, 0, true);
    }

    // Auto-refresh expired session once
    if (response.status === 401 && retryOnAuthFailure) {
      this.resetSession();
      await this.initSession();
      return this.query(trimmed, false);
    }

    if (!response.ok) {
      let detail = 'Query submission failed';
      try {
        const body = await response.json();
        if (body?.detail) {
          detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
        }
      } catch {
        // Ignore parse error
      }

      if (response.status === 429) {
        throw new MobileAssistantError('Rate limit exceeded (10 queries/min). Please pause for a moment.', 429, false);
      }
      if (response.status === 504) {
        throw new MobileAssistantError('Assistant service timed out. Please try a simpler question.', 504, true);
      }
      throw new MobileAssistantError(`Query error (${response.status}): ${detail}`, response.status, response.status >= 500);
    }

    const data: MobileAssistantResponse = await response.json();
    return data;
  }
}

export const mobileAssistantService = new MobileAssistantService();

export const MOBILE_SUGGESTED_QUESTIONS = [
  'Why do landslides happen and what early physical signals precede slope failure?',
  'How do rainfall intensity, duration, and soil moisture influence slope stability?',
  'How do GIS spatial layers and terrain factors combine to produce landslide susceptibility maps?',
  'How does machine learning predict landslide risk across the three-layer pipeline?',
  'How do landslide risk maps and sensor thresholds translate into operational early-warning decisions?',
] as const;
