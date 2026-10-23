export interface AuditEntry {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_id: string | null;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  created_at: string;
}
