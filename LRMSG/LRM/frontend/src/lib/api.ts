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
