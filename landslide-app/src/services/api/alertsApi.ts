import { apiClient } from './client';
import { API_CONFIG } from './apiConfig';
import type { Alert, ApiResponse } from './types';

export async function getAllAlerts(): Promise<ApiResponse<Alert[]>> {
  return apiClient.get<Alert[]>(API_CONFIG.endpoints.alerts.base);
}

export async function acknowledgeAlert(
  alertId: string
): Promise<ApiResponse<{ status: string; alert: Alert }>> {
  return apiClient.post<{ status: string; alert: Alert }>(
    `${API_CONFIG.endpoints.alerts.base}/${alertId}/acknowledge`
  );
}

export async function resolveAlert(
  alertId: string
): Promise<ApiResponse<{ status: string; alert: Alert }>> {
  return apiClient.post<{ status: string; alert: Alert }>(
    `${API_CONFIG.endpoints.alerts.base}/${alertId}/resolve`
  );
}

export async function markAlertResponding(
  alertId: string
): Promise<ApiResponse<{ status: string; alert: Alert }>> {
  return apiClient.post<{ status: string; alert: Alert }>(
    `${API_CONFIG.endpoints.alerts.base}/${alertId}/responding`
  );
}