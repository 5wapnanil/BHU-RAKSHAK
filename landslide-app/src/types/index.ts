export type EmergencyType = 'fire' | 'earthquake' | 'flood' | 'landslide' | 'cyclone' | 'other';

export type RequestStatus = 'pending' | 'in_progress' | 'resolved' | 'cancelled';

export type SyncStatus = 'local_only' | 'syncing' | 'server_confirmed' | 'sync_failed';

export type RequestType = 'evacuation' | 'help' | 'relief' | 'volunteer' | 'field_report';

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  avatarUrl?: string;
}

export interface Location {
  latitude: number;
  longitude: number;
  address?: string;
}

export interface LocationCoords {
  latitude: number;
  longitude: number;
}

export interface EmergencyRequest {
  id: string;
  type: RequestType;
  emergencyType: EmergencyType;
  status: RequestStatus;
  userId: string;
  location: Location;
  description?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Alert {
  id: string;
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  location?: string;
  createdAt: string;
}

export interface Shelter {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  capacity: number;
  currentOccupancy: number;
  contactPhone?: string;
}

export interface WeatherData {
  temperature: number;
  condition: string;
  windSpeed: number;
  humidity: number;
  rainChance: number;
  direction: string;
}

export interface SafetyTip {
  id: string;
  title: string;
  description: string;
  category: string;
  iconUrl?: string;
}

// ──────────────────────────────────────────────
// STEP 4 – local-workflow domain types
// ──────────────────────────────────────────────

/** Form data collected by Call for Evacuation screen */
export interface EvacuationFormData {
  location: string;
  numberOfPeople: string;
  emergencyType: EmergencyType | '';
  hasVulnerable: boolean | null;
  contactName: string;
  contactPhone: string;
  additionalInfo: string;
  gpsCoords?: LocationCoords;
}

/** Form data collected by Call for Help screen */
export interface HelpFormData {
  location: string;
  category: EmergencyType | '';
  severity: 'low' | 'medium' | 'high' | 'critical' | '';
  peopleAffected: string;
  description: string;
  contactName: string;
  contactPhone: string;
  gpsCoords?: LocationCoords;
}

/** Form data collected by Request Relief screen */
export interface ReliefFormData {
  location: string;
  reliefCategory: string;
  requiredItems: string;
  quantity: string;
  peopleAffected: string;
  severity: 'low' | 'medium' | 'high' | 'critical' | '';
  hasVulnerable: boolean | null;
  contactName: string;
  contactPhone: string;
  additionalInfo: string;
  gpsCoords?: LocationCoords;
}

/** Form data collected by Volunteer for Evacuation screen */
export interface EvacuationVolunteerFormData {
  name: string;
  phone: string;
  currentLocation: string;
  hasTransport: boolean | null;
  capacity: string;
  capabilities: string[];
  availability: string;
  gpsCoords?: LocationCoords;
}

/** Form data collected by Volunteer for Relief screen */
export interface ReliefVolunteerFormData {
  name: string;
  phone: string;
  location: string;
  category: string;
  quantity: string;
  availability: string;
  description: string;
  gpsCoords?: LocationCoords;
}

// ── Local store request wrappers ──

export interface LocalEvacuationRequest {
  id: string;
  type: 'evacuation';
  status: RequestStatus;
  syncStatus: SyncStatus;
  formData: EvacuationFormData;
  createdAt: string;
  updatedAt: string;
}

export interface LocalHelpRequest {
  id: string;
  type: 'help';
  status: RequestStatus;
  syncStatus: SyncStatus;
  formData: HelpFormData;
  createdAt: string;
  updatedAt: string;
}

export interface LocalReliefRequest {
  id: string;
  type: 'relief';
  status: RequestStatus;
  syncStatus: SyncStatus;
  formData: ReliefFormData;
  createdAt: string;
  updatedAt: string;
}

export interface LocalEvacuationVolunteer {
  id: string;
  type: 'evacuation_volunteer';
  status: RequestStatus;
  syncStatus: SyncStatus;
  formData: EvacuationVolunteerFormData;
  createdAt: string;
  updatedAt: string;
}

export interface LocalReliefVolunteer {
  id: string;
  type: 'relief_volunteer';
  status: RequestStatus;
  syncStatus: SyncStatus;
  formData: ReliefVolunteerFormData;
  createdAt: string;
  updatedAt: string;
}

/** Form data collected by Field Report screen */
export interface FieldReportFormData {
  notes?: string;
  locationName?: string;
  reporterName?: string;
  reporterPhone?: string;
  photoUri?: string;
  photoFileName?: string;
  photoMimeType?: string;
  gpsCoords?: LocationCoords;
}

export interface LocalFieldReport {
  id: string;
  serverId?: string;
  type: 'field_report';
  status: RequestStatus;
  syncStatus: SyncStatus;
  formData: FieldReportFormData;
  createdAt: string;
  updatedAt: string;
  errorDetail?: string;
}

export type LocalRequest =
  | LocalEvacuationRequest
  | LocalHelpRequest
  | LocalReliefRequest
  | LocalEvacuationVolunteer
  | LocalReliefVolunteer
  | LocalFieldReport;

// ── Action / reducer types for the local store ──

export type LocalRequestAction =
  | { type: 'ADD_REQUEST'; payload: LocalRequest }
  | { type: 'UPDATE_STATUS'; payload: { id: string; status: RequestStatus } }
  | { type: 'UPDATE_SYNC_STATUS'; payload: { id: string; syncStatus: SyncStatus } }
  | { type: 'DELETE_REQUEST'; payload: { id: string } }
  | { type: 'SET_INITIAL_STATE'; payload: LocalRequestState };

export interface LocalRequestState {
  requests: LocalRequest[];
  volunteers: Array<LocalEvacuationVolunteer | LocalReliefVolunteer>;
}
