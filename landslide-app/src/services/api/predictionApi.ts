import { apiClient } from './client';
import { API_CONFIG } from './apiConfig';
import type {
  PredictionResponse,
  LocationPredictionRequest,
  CustomPredictionRequest,
  EnvironmentalDataResponse,
  NerRiskDataResponse,
  NearbyRiskResponse,
  ApiResponse,
} from './types';

export async function getLocationPrediction(
  request: LocationPredictionRequest
): Promise<ApiResponse<PredictionResponse>> {
  return apiClient.post<PredictionResponse>(
    API_CONFIG.endpoints.prediction.location,
    request
  );
}

export async function getCustomPrediction(
  request: CustomPredictionRequest
): Promise<ApiResponse<PredictionResponse>> {
  return apiClient.post<PredictionResponse>(
    API_CONFIG.endpoints.prediction.custom,
    request
  );
}

export async function getEnvironmentalData(
  latitude: number,
  longitude: number
): Promise<ApiResponse<EnvironmentalDataResponse>> {
  return apiClient.post<EnvironmentalDataResponse>(
    API_CONFIG.endpoints.environment,
    { latitude, longitude }
  );
}

export async function getNerRiskData(): Promise<ApiResponse<NerRiskDataResponse>> {
  return apiClient.get<NerRiskDataResponse>(
    API_CONFIG.endpoints.riskZones.nerRiskData
  );
}

export async function getNearbyRisk(
  lat: number,
  lng: number,
  radiusKm: number = 150
): Promise<ApiResponse<NearbyRiskResponse>> {
  return apiClient.get<NearbyRiskResponse>(
    `${API_CONFIG.endpoints.riskZones.nearby}?lat=${lat}&lng=${lng}&radius_km=${radiusKm}`
  );
}