export interface ApiError {
  message: string;
  code: string;
  status?: number;
}

export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
  success: boolean;
}

export interface HealthResponse {
  status: string;
}

/**
 * Raw ML feature vector for POST /prediction/ endpoint.
 *
 * WARNING: This type documents the backend schema but is NOT used by any
 * mobile screen. The backend Pydantic model uses aliases (e.g. _rzsm_mean_)
 * that differ from these field names. Do NOT call this endpoint from mobile
 * without implementing explicit alias mapping.
 *
 * Mobile screens should use LocationPredictionRequest or CustomPredictionRequest.
 */
export interface PredictionRequest {
  rzsm_1: number;
  rzsm_2: number;
  rzsm_3: number;
  cumulative_rainfall_3d_mm: number;
  rzsm_mean: number;
  rzsm_range: number;
  rzsm_surface_deep_diff: number;
  rain_rzsm_interaction: number;
  previous_rzsm: number;
  previous_rzsm_2: number;
  previous_rzsm_3: number;
  previous_rainfall: number;
  rzsm_0_100: number;
  elevation_m: number;
  slope_deg: number;
  soil_type_wrb: string;
}

export interface LocationPredictionRequest {
  latitude: number;
  longitude: number;
}

export interface CustomPredictionRequest {
  rainfall: number;
  soilMoisture: number;
  slope: number;
  elevation: number;
  soilType: string;
}

export interface CalibrationDetail {
  method: string;
  a: number;
  b: number;
}

export interface XGBoostDetail {
  raw_probability: number;
  calibrated_probability: number;
  prediction: number;
  calibration: CalibrationDetail;
}

export interface AHCDetail {
  cluster: number;
  susceptibility: number;
  category: string;
}

export interface FinalDecisionDetail {
  raw_probability: number;
  calibrated_probability: number;
  prediction: number;
  calibration: CalibrationDetail;
}

export interface PredictionResponse {
  xgboost: XGBoostDetail;
  ahc: AHCDetail;
  final_decision: FinalDecisionDetail;
  prediction: number;
  probability: number;
  features: Record<string, unknown> | null;
}

export interface EnvironmentalDataRequest {
  latitude: number;
  longitude: number;
}

export interface EnvironmentalDataResponse {
  latitude: number;
  longitude: number;
  observed_at_utc: string;
  rzsm_1: number;
  rzsm_2: number;
  rzsm_3: number;
  rzsm_0_100: number;
  cumulative_rainfall_3d_mm: number;
  rzsm_mean: number;
  rzsm_range: number;
  rzsm_surface_deep_diff: number;
  rain_rzsm_interaction: number;
  previous_rzsm: number;
  previous_rzsm_2: number;
  previous_rzsm_3: number;
  previous_rainfall: number;
  elevation_m: number;
  slope_deg: number;
  soil_type_wrb: string;
}

export interface Alert {
  id: string;
  location_id: string;
  location_name: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
  severity: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
  risk_probability: number;
  trigger: string;
  contributing_factors: string;
  rainfall: number;
  soil_condition: number;
  slope_condition: number;
  road_status: string;
  response_priority: string;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'UNDER_RESPONSE' | 'RESOLVED';
  created_at: string;
  updated_at: string;
  lifecycle: Array<{ state: string; timestamp: string }>;
  notifications: {
    district_admin: string;
    disaster_management: string;
    local_community: string;
  };
}

export interface SyncOperation {
  id: string;
  operation: 'CREATE' | 'UPDATE' | 'DELETE';
  entity: string;
  payload: Record<string, unknown>;
  createdAt: string;
}

export interface SyncBatch {
  operations: SyncOperation[];
}

export interface SyncResponse {
  success: boolean;
  success_ids: string[];
  failed_ids: string[];
}

export interface RiskZone {
  name: string;
  state: string;
  lat: number;
  lng: number;
  elevation: number;
  slope: number;
  soil_type: string;
  risk_probability: number | null;
  risk_level: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'LOW' | 'UNAVAILABLE';
  risk_color: string;
  xgboost_probability?: number | null;
  ahc_susceptibility?: number | null;
  ahc_category?: string | null;
  ahc_cluster?: number | null;
  rainfall_mm: number;
  soil_moisture: number;
  distance_km?: number;
  prediction_status?: string;
}

export interface NerRiskDataResponse {
  zones: RiskZone[];
  summary: {
    total: number;
    critical_count: number;
    high_count: number;
    moderate_count: number;
    critical_zones: Array<{ name: string; state: string; risk_probability: number }>;
    high_zones: Array<{ name: string; state: string; risk_probability: number }>;
  };
  risk_grading: Record<string, { threshold: string; color: string; label: string }>;
}

export interface NearbyRiskResponse {
  user_location: { lat: number; lng: number };
  user_zone: RiskZone | null;
  nearby_zones: RiskZone[];
  high_risk_ner: RiskZone[];
  summary: {
    total_zones_evaluated: number;
    critical_count: number;
    high_count: number;
    moderate_count: number;
    low_count: number;
  };
  risk_grading: Record<string, { threshold: string; color: string; label: string }>;
}