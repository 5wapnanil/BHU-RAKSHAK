export interface EmergencyRequest {
  id: string;
  client_op_id: string | null;
  request_type: string;
  status: string;
  server_status: string | null;
  severity: string | null;
  location_text: string | null;
  people_affected: number | null;
  contact_name: string | null;
  contact_phone: string | null;
  payload: Record<string, unknown> | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface VolunteerProfile {
  id: string;
  user_id: string;
  skills: string[];
  has_transport: boolean | null;
  capacity: number | null;
  availability: string | null;
  status: string;
  is_active: boolean;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Assignment {
  id: string;
  request_id: string | null;
  volunteer_id: string | null;
  resource_id: string | null;
  assignment_type: string;
  status: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReliefResource {
  id: string;
  resource_type: string;
  description: string | null;
  quantity: number | null;
  unit: string | null;
  available_quantity: number | null;
  provider_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Shelter {
  id: string;
  name: string;
  location: string | null;
  address: string | null;
  capacity: number;
  current_occupancy: number;
  facilities: Record<string, unknown> | null;
  contact_phone: string | null;
  status: string;
  operated_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface HealthResponse {
  status: string;
  database: {
    postgresql?: string;
    postgis?: string;
    table_count?: number | string;
  };
}

export interface SyncHealthResponse {
  status: string;
  db_connected: boolean;
  mode: string;
}
