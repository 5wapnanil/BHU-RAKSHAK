import { API_CONFIG } from './apiConfig';
import type { ApiError, ApiResponse } from './types';

const DEV = __DEV__;

function devLog(...args: unknown[]) {
  if (DEV) console.log('[API]', ...args);
}

function devWarn(...args: unknown[]) {
  if (DEV) console.warn('[API]', ...args);
}

class ApiClient {
  private baseUrl: string;
  private timeout: number;

  constructor() {
    this.baseUrl = API_CONFIG.baseUrl;
    this.timeout = API_CONFIG.timeout;
    devLog('baseUrl =', this.baseUrl);
  }

  setBaseUrl(url: string) {
    this.baseUrl = url;
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: unknown
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const startedAt = Date.now();
    devLog(`${method} ${url} [timeout=${this.timeout}ms]`);

    const controller = new AbortController();
    let timedOut = false;
    const timeoutId = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, this.timeout);

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      const options: RequestInit = {
        method,
        headers,
        signal: controller.signal,
      };

      if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(url, options);
      clearTimeout(timeoutId);

      const elapsed = Date.now() - startedAt;
      devLog(`${method} ${url} → ${response.status} (${elapsed}ms)`);

      if (!response.ok) {
        let errorBody;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = { detail: response.statusText };
        }

        devWarn(`${method} ${url} HTTP ${response.status}:`, errorBody);

        return {
          data: null,
          error: {
            message: errorBody?.detail || errorBody?.message || 'Request failed',
            code: `HTTP_${response.status}`,
            status: response.status,
          },
          success: false,
        };
      }

      const result = await response.json();
      return {
        data: result,
        error: null,
        success: true,
      };
    } catch (error: unknown) {
      clearTimeout(timeoutId);
      const fetchError = error as { name?: string; message?: string };
      
      const elapsed = Date.now() - startedAt;
      devWarn(`${method} ${url} ERROR (${elapsed}ms):`, fetchError?.name, fetchError?.message);

      if (timedOut || fetchError?.name === 'AbortError') {
        return {
          data: null,
          error: {
            message: `Request timed out after ${elapsed}ms (limit: ${this.timeout}ms)`,
            code: 'TIMEOUT',
          },
          success: false,
        };
      }

      if (
        fetchError?.message?.includes('Network') ||
        fetchError?.message?.toLowerCase().includes('fetch')
      ) {
        return {
          data: null,
          error: {
            message: `Network error (${elapsed}ms): ${fetchError?.message}`,
            code: 'NETWORK_ERROR',
          },
          success: false,
        };
      }

      return {
        data: null,
        error: {
          message: fetchError?.message || 'Unexpected error',
          code: 'UNKNOWN',
        },
        success: false,
      };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>('GET', endpoint);
  }

  async post<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>('POST', endpoint, data);
  }

  async put<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', endpoint, data);
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', endpoint);
  }

  async patch<T>(endpoint: string, data?: unknown): Promise<ApiResponse<T>> {
    return this.request<T>('PATCH', endpoint, data);
  }
}

export const apiClient = new ApiClient();