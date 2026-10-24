import { Platform } from 'react-native';

const EMULATOR_BASE_URL = 'http://10.0.2.2:8000';
const LAN_BASE_URL = 'http://192.168.0.102:8000';

export function isAndroidEmulator(): boolean {
  if (Platform.OS !== 'android') return false;

  const androidConstants = Platform.constants as Record<string, unknown>;
  const model = String(androidConstants.Model ?? '');
  const fingerprint = String(androidConstants.Fingerprint ?? '');

  return /sdk|emulator|generic|genymotion|vbox/i.test(model + fingerprint);
}

/**
 * Validates and resolves the API base URL according to the active build environment.
 *
 * SECURITY & DEPLOYMENT INVARIANTS:
 * 1. Development mode (__DEV__ === true):
 *    - Respects EXPO_PUBLIC_API_URL override if present.
 *    - Automatically routes Android emulator traffic to http://10.0.2.2:8000.
 *    - Routes physical LAN device traffic to http://192.168.0.102:8000.
 *    - Routes web browser preview to window.location.hostname:8000.
 * 2. Production / Release mode (__DEV__ === false):
 *    - REQUIRES an explicit EXPO_PUBLIC_API_URL environment variable.
 *    - Disallows empty base URLs or silent fallback to localhost.
 *    - Enforces HTTPS scheme (https://) for external production endpoints.
 */
export function resolveApiBaseUrl(
  isDev: boolean = typeof __DEV__ !== 'undefined' ? __DEV__ : true,
  envApiUrl?: string
): string {
  const raw =
    envApiUrl !== undefined
      ? envApiUrl
      : typeof process !== 'undefined'
      ? process.env?.EXPO_PUBLIC_API_URL
      : undefined;
  const configured = raw?.trim().replace(/\/+$/, '');

  if (!isDev) {
    if (!configured) {
      throw new Error(
        'Configuration Error: Production mobile release build requires EXPO_PUBLIC_API_URL to be configured with an HTTPS backend endpoint.'
      );
    }
    if (!configured.startsWith('https://')) {
      // Permit local test loopback addresses if explicitly configured during release-mode testing
      const isLocalLoopback =
        configured.startsWith('http://localhost') || configured.startsWith('http://127.0.0.1');
      if (!isLocalLoopback) {
        throw new Error(
          `Security Error: Insecure production API URL '${configured}'. Production release builds must use an HTTPS endpoint.`
        );
      }
    }
    return configured;
  }

  // Development mode
  if (configured) {
    return configured;
  }
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
  baseUrl: resolveApiBaseUrl(),
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
    assistant: {
      threads: '/api/assistant/threads',
      query: '/api/assistant/query',
    },
  },
};