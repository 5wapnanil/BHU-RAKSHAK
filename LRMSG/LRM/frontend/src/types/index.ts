export type RiskLevel = "low" | "moderate" | "high" | "critical";

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface LocationData extends Coordinates {
  name: string;
  state: string;
  district: string;
}

export interface EnvironmentalFeatures {
  rainfall: number;
  soilMoisture: number;
  slope: number;
  elevation: number;
  ndvi: number;
  temperature: number;
  soilType: string;
}

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

export interface CalibrationInfo {
  method: string;
  a: number;
  b: number;
}

export interface PredictionLayerResult {
  raw_probability: number;
  calibrated_probability: number;
  prediction: number;
  calibration: CalibrationInfo;
}

export interface AHCResult {
  cluster: number;
  susceptibility: number;
  category: string;
}

export interface PredictionResult {
  prediction: number;
  probability: number;
}

export interface PredictionResponse {
  location?: LocationData;
  features: EnvironmentalFeatures;
  prediction: PredictionResult;

  xgboost: PredictionLayerResult;
  ahc: AHCResult;

  final_decision: PredictionLayerResult;

  timestamp?: string;
}
export interface Zone {
  id: number;
  name: string;
  state: string;
  lat: number;
  lng: number;
  risk_score: number;
  risk_level: RiskLevel;
  features?: {
    rainfall: number;
    soilMoisture: number;
    slope: number;
    elevation: number;
    soilType: string;
  };
}

export interface Alert {
  id: string;
  severity: "info" | "moderate" | "high" | "critical";
  location: string;
  message: string;
  timestamp: string;
  riskChange?: { from: RiskLevel; to: RiskLevel };
}

export interface Report {
  id: string;
  location: string;
  date: string;
  riskLevel: RiskLevel;
  probability: number;
  status: "generated" | "pending";
}

export interface SystemStatus {
  backend: "online" | "offline";
  mlModel: "loaded" | "unloaded";
  lastUpdate: string;
  totalPredictions: number;
  modelVersion: string;
}
