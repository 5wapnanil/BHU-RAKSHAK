export type Severity = "CRITICAL" | "HIGH" | "MODERATE" | "LOW";
export type AlertStatus = "ACTIVE" | "ACKNOWLEDGED" | "UNDER_RESPONSE" | "RESOLVED";

export interface AlertLifecycle {
  state: string;
  timestamp: string;
}

export interface AlertNotifications {
  district_admin: string;
  disaster_management: string;
  local_community: string;
}

export interface Alert {
  id: string;
  location_id: string;
  location_name: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
  severity: Severity;
  risk_probability: number;
  trigger: string;
  contributing_factors: string;
  rainfall: number;
  soil_condition: number;
  slope_condition: number;
  road_status: string;
  response_priority: string;
  status: AlertStatus;
  created_at: string;
  updated_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  lifecycle: AlertLifecycle[];
  notifications: AlertNotifications;
}

export interface WebSocketMessage {
  type: string;
  alerts?: Alert[];
  alert?: Alert;
  demo?: boolean;
}
