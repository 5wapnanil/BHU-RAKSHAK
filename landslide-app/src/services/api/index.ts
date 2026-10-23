export { apiClient } from './client';
export { API_CONFIG } from './apiConfig';
export { submitFieldReportApi, fetchFieldReportsApi } from './fieldReportApi';
export type { FieldReportResponseData } from './fieldReportApi';

export {
  syncIncidents,
  createIncidentReportOperation,
  createSyncBatch,
} from './syncApi';

export {
  getAllAlerts,
  acknowledgeAlert,
  resolveAlert,
  markAlertResponding,
} from './alertsApi';

export {
  getLocationPrediction,
  getCustomPrediction,
  getEnvironmentalData,
  getNerRiskData,
  getNearbyRisk,
} from './predictionApi';

export {
  getAssignments,
  getAssignment,
  updateAssignmentStatus,
  getReliefResources,
  getReliefResource,
  createReliefResource,
  allocateReliefResource,
  releaseReliefResource,
  getShelters,
  getShelter,
  createShelter,
  updateShelter,
} from './operationsApi';

export type {
  Assignment,
  ReliefResource,
  Shelter,
  ShelterCreate,
  ShelterUpdate,
  ReliefResourceCreate,
  ResourceAllocateRequest,
} from './operationsApi';

export type {
  ApiError,
  ApiResponse,
  HealthResponse,
  PredictionRequest,
  LocationPredictionRequest,
  CustomPredictionRequest,
  CalibrationDetail,
  XGBoostDetail,
  AHCDetail,
  FinalDecisionDetail,
  PredictionResponse,
  EnvironmentalDataRequest,
  EnvironmentalDataResponse,
  Alert,
  SyncOperation,
  SyncBatch,
  SyncResponse,
  RiskZone,
  NerRiskDataResponse,
  NearbyRiskResponse,
} from './types';