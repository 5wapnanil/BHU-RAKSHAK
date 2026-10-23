import { Platform } from 'react-native';
import { API_CONFIG } from './apiConfig';
import { apiClient } from './client';
import type { ApiResponse } from './types';
import type { FieldReportFormData } from '../../types';

export interface FieldReportResponseData {
  id: string;
  notes: string | null;
  location_name: string | null;
  latitude: number | null;
  longitude: number | null;
  photo_url: string | null;
  reporter_name: string | null;
  reporter_phone: string | null;
  submitted_at: string;
  review_status: string;
  ai_hazard_level: string;
  ai_confidence: number | null;
  ai_summary: string | null;
  ai_detected_hazards: string[];
  ai_status?: string;
  ai_analyzed_at?: string | null;
}

export async function submitFieldReportApi(
  formData: FieldReportFormData
): Promise<ApiResponse<FieldReportResponseData>> {
  const endpoint = API_CONFIG.endpoints.fieldReports;

  // Case 1: Photo is attached -> Submit via multipart/form-data
  if (formData.photoUri) {
    const url = `${API_CONFIG.baseUrl}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);

    try {
      const data = new FormData();
      if (formData.notes) data.append('notes', formData.notes);
      if (formData.locationName) data.append('location_name', formData.locationName);
      if (formData.gpsCoords?.latitude !== undefined) {
        data.append('latitude', String(formData.gpsCoords.latitude));
      }
      if (formData.gpsCoords?.longitude !== undefined) {
        data.append('longitude', String(formData.gpsCoords.longitude));
      }
      if (formData.reporterName) data.append('reporter_name', formData.reporterName);
      if (formData.reporterPhone) data.append('reporter_phone', formData.reporterPhone);

      const filename =
        formData.photoFileName ||
        formData.photoUri.split('/').pop() ||
        'field_observation.jpg';
      const match = /\.(\w+)$/.exec(filename);
      const mimeType =
        formData.photoMimeType || (match ? `image/${match[1].toLowerCase()}` : 'image/jpeg');
      const normalizedMime = mimeType === 'image/jpg' ? 'image/jpeg' : mimeType;

      // Handle web/browser/blob URIs vs React Native native { uri, name, type }
      const isWebOrBlob =
        Platform.OS === 'web' ||
        formData.photoUri.startsWith('blob:') ||
        formData.photoUri.startsWith('data:') ||
        formData.photoUri.startsWith('http://') ||
        formData.photoUri.startsWith('https://');

      if (isWebOrBlob && typeof fetch === 'function') {
        try {
          const res = await fetch(formData.photoUri);
          const blob = await res.blob();
          data.append('photo', blob, filename);
        } catch {
          data.append('photo', {
            uri: formData.photoUri,
            name: filename,
            type: normalizedMime,
          } as any);
        }
      } else {
        data.append('photo', {
          uri: formData.photoUri,
          name: filename,
          type: normalizedMime,
        } as any);
      }

      // Note: Do NOT set Content-Type header so fetch sets boundary correctly
      const response = await fetch(url, {
        method: 'POST',
        body: data,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errBody;
        try {
          errBody = await response.json();
        } catch {
          errBody = { detail: response.statusText };
        }
        return {
          data: null,
          error: {
            message: errBody?.detail || errBody?.message || `HTTP ${response.status}`,
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
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err?.name === 'AbortError') {
        return {
          data: null,
          error: { message: 'Upload request timed out', code: 'TIMEOUT' },
          success: false,
        };
      }
      return {
        data: null,
        error: {
          message: err?.message || 'Network request failed',
          code: 'NETWORK_ERROR',
        },
        success: false,
      };
    }
  }

  // Case 2: No photo -> Clean JSON payload
  const jsonBody = {
    notes: formData.notes?.trim() ? formData.notes.trim() : null,
    location_name: formData.locationName?.trim() ? formData.locationName.trim() : null,
    latitude: formData.gpsCoords?.latitude ?? null,
    longitude: formData.gpsCoords?.longitude ?? null,
    reporter_name: formData.reporterName?.trim() ? formData.reporterName.trim() : null,
    reporter_phone: formData.reporterPhone?.trim() ? formData.reporterPhone.trim() : null,
  };

  return apiClient.post<FieldReportResponseData>(endpoint, jsonBody);
}

export async function fetchFieldReportsApi(): Promise<
  ApiResponse<{ items: FieldReportResponseData[]; total: number }>
> {
  return apiClient.get<{ items: FieldReportResponseData[]; total: number }>(
    `${API_CONFIG.endpoints.fieldReports}?limit=50`
  );
}
