import { apiClient } from './client';
import { API_CONFIG } from './apiConfig';
import type { ApiResponse } from './types';

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

export interface ShelterCreate {
  name: string;
  address?: string;
  capacity?: number;
  contact_phone?: string;
  operated_by?: string;
}

export interface ShelterUpdate {
  name?: string;
  address?: string;
  capacity?: number;
  contact_phone?: string;
  status?: string;
}

export interface ReliefResourceCreate {
  resource_type: string;
  description?: string;
  quantity?: number;
  unit?: string;
  latitude?: number;
  longitude?: number;
}

export interface ResourceAllocateRequest {
  request_id: string;
  quantity: number;
  notes?: string;
}

// ── Assignments ──

export async function getAssignments(limit = 100): Promise<ApiResponse<Assignment[]>> {
  return apiClient.get<Assignment[]>(`${API_CONFIG.endpoints.assignments}?limit=${limit}`);
}

export async function getAssignment(id: string): Promise<ApiResponse<Assignment>> {
  return apiClient.get<Assignment>(`${API_CONFIG.endpoints.assignments}/${id}`);
}

export async function updateAssignmentStatus(
  id: string,
  status: string,
): Promise<ApiResponse<Assignment>> {
  return apiClient.patch<Assignment>(`${API_CONFIG.endpoints.assignments}/${id}/status`, { status });
}

// ── Relief Resources ──

export async function getReliefResources(limit = 100): Promise<ApiResponse<ReliefResource[]>> {
  return apiClient.get<ReliefResource[]>(`${API_CONFIG.endpoints.reliefResources}?limit=${limit}`);
}

export async function getReliefResource(id: string): Promise<ApiResponse<ReliefResource>> {
  return apiClient.get<ReliefResource>(`${API_CONFIG.endpoints.reliefResources}/${id}`);
}

export async function createReliefResource(
  data: ReliefResourceCreate,
): Promise<ApiResponse<ReliefResource>> {
  return apiClient.post<ReliefResource>(API_CONFIG.endpoints.reliefResources, data);
}

export async function allocateReliefResource(
  resourceId: string,
  data: ResourceAllocateRequest,
): Promise<ApiResponse<Assignment>> {
  return apiClient.post<Assignment>(
    `${API_CONFIG.endpoints.reliefResources}/${resourceId}/allocate`,
    data,
  );
}

export async function releaseReliefResource(assignmentId: string): Promise<ApiResponse<unknown>> {
  return apiClient.post<unknown>(
    `${API_CONFIG.endpoints.reliefResources}/allocations/${assignmentId}/release`,
  );
}

// ── Shelters ──

export async function getShelters(limit = 100): Promise<ApiResponse<Shelter[]>> {
  return apiClient.get<Shelter[]>(`${API_CONFIG.endpoints.shelters}?limit=${limit}`);
}

export async function getShelter(id: string): Promise<ApiResponse<Shelter>> {
  return apiClient.get<Shelter>(`${API_CONFIG.endpoints.shelters}/${id}`);
}

export async function createShelter(data: ShelterCreate): Promise<ApiResponse<Shelter>> {
  return apiClient.post<Shelter>(API_CONFIG.endpoints.shelters, data);
}

export async function updateShelter(
  id: string,
  data: ShelterUpdate,
): Promise<ApiResponse<Shelter>> {
  return apiClient.patch<Shelter>(`${API_CONFIG.endpoints.shelters}/${id}`, data);
}
