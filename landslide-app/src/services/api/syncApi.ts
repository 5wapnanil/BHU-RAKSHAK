import { apiClient } from './client';
import { API_CONFIG } from './apiConfig';
import type { SyncBatch, SyncResponse, ApiResponse } from './types';
import type {
  LocalRequest,
  LocalEvacuationRequest,
  LocalHelpRequest,
  LocalReliefRequest,
  LocalEvacuationVolunteer,
  LocalReliefVolunteer,
} from '../../types';

export async function syncIncidents(batch: SyncBatch): Promise<ApiResponse<SyncResponse>> {
  return apiClient.post<SyncResponse>(API_CONFIG.endpoints.sync, batch);
}

function mapEvacuationPayload(req: LocalEvacuationRequest): Record<string, unknown> {
  return {
    request_type: 'evacuation',
    location: req.formData.location,
    numberOfPeople: req.formData.numberOfPeople,
    emergencyType: req.formData.emergencyType,
    hasVulnerable: req.formData.hasVulnerable,
    contactName: req.formData.contactName,
    contactPhone: req.formData.contactPhone,
    additionalInfo: req.formData.additionalInfo,
    gpsCoords: req.formData.gpsCoords,
  };
}

function mapHelpPayload(req: LocalHelpRequest): Record<string, unknown> {
  return {
    request_type: 'help',
    location: req.formData.location,
    category: req.formData.category,
    severity: req.formData.severity,
    peopleAffected: req.formData.peopleAffected,
    description: req.formData.description,
    contactName: req.formData.contactName,
    contactPhone: req.formData.contactPhone,
    gpsCoords: req.formData.gpsCoords,
  };
}

function mapEvacuationVolunteerPayload(req: LocalEvacuationVolunteer): Record<string, unknown> {
  return {
    request_type: 'evacuation_volunteer',
    name: req.formData.name,
    phone: req.formData.phone,
    currentLocation: req.formData.currentLocation,
    hasTransport: req.formData.hasTransport,
    capacity: req.formData.capacity,
    capabilities: req.formData.capabilities,
    availability: req.formData.availability,
    gpsCoords: req.formData.gpsCoords,
  };
}

function mapReliefVolunteerPayload(req: LocalReliefVolunteer): Record<string, unknown> {
  return {
    request_type: 'relief_volunteer',
    name: req.formData.name,
    phone: req.formData.phone,
    location: req.formData.location,
    category: req.formData.category,
    quantity: req.formData.quantity,
    availability: req.formData.availability,
    description: req.formData.description,
    gpsCoords: req.formData.gpsCoords,
  };
}

function mapReliefPayload(req: LocalReliefRequest): Record<string, unknown> {
  return {
    request_type: 'relief',
    location: req.formData.location,
    reliefCategory: req.formData.reliefCategory,
    requiredItems: req.formData.requiredItems,
    quantity: req.formData.quantity,
    peopleAffected: req.formData.peopleAffected,
    severity: req.formData.severity,
    hasVulnerable: req.formData.hasVulnerable,
    contactName: req.formData.contactName,
    contactPhone: req.formData.contactPhone,
    additionalInfo: req.formData.additionalInfo,
    gpsCoords: req.formData.gpsCoords,
  };
}

function mapLocalRequestToIncidentPayload(request: LocalRequest): Record<string, unknown> {
  switch (request.type) {
    case 'evacuation':
      return mapEvacuationPayload(request);
    case 'help':
      return mapHelpPayload(request);
    case 'relief':
      return mapReliefPayload(request);
    case 'evacuation_volunteer':
      return mapEvacuationVolunteerPayload(request);
    case 'relief_volunteer':
      return mapReliefVolunteerPayload(request);
    case 'field_report':
      return {
        notes: request.formData.notes,
        location: request.formData.locationName,
        contactName: request.formData.reporterName,
        contactPhone: request.formData.reporterPhone,
        gpsCoords: request.formData.gpsCoords,
      };
  }
}

export function createIncidentReportOperation(
  request: LocalRequest
) {
  return {
    id: request.id,
    operation: 'CREATE' as const,
    entity: request.type === 'field_report' ? 'field_report' : 'incident_report',
    payload: mapLocalRequestToIncidentPayload(request),
    createdAt: request.createdAt,
  };
}

export function createSyncBatch(operations: SyncBatch['operations']): SyncBatch {
  return { operations };
}
