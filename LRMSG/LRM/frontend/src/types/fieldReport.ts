export type ReviewStatus = 'pending' | 'under_review' | 'verified' | 'rejected' | 'needs_inspection';

export type HazardLevel = 'low' | 'moderate' | 'high' | 'critical' | 'indeterminate';

export type AIScreeningStatus = 'pending' | 'completed' | 'failed' | 'unavailable' | 'processing' | 'not_configured';

export interface FieldReport {
  id: string;
  client_op_id?: string | null;
  title?: string | null;
  photo_url?: string | null;
  thumbnail_url?: string | null;
  notes: string;
  location_name: string;
  latitude?: number | null;
  longitude?: number | null;
  reporter_name?: string | null;
  reporter_phone?: string | null;
  submitted_at: string;

  // AI-assisted preliminary screening (Gemma multimodal integration)
  ai_status?: AIScreeningStatus;
  ai_screening_status: AIScreeningStatus;
  ai_hazard_level?: HazardLevel | null;
  ai_confidence?: number | null;
  ai_detected_hazards?: string[] | null;
  ai_summary?: string | null;
  ai_analyzed_at?: string | null;
  ai_disclaimer?: string;

  // Human review and administrative decision
  review_status: ReviewStatus;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  admin_notes?: string | null;
  linked_incident_id?: string | null;
}

export interface FieldReportSummary {
  total: number;
  pending: number;
  under_review: number;
  verified: number;
  rejected: number;
}
