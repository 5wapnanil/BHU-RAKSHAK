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
  if (typeof process !== 'undefined' && process.env?.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL.replace(/\/+$/, '');
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
    assistant: {
      threads: '/api/assistant/threads',
      query: '/api/assistant/query',
    },
  },
};