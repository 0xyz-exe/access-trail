export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
}

export interface Identity {
  id: string;
  username: string;
  email?: string;
  full_name: string;
  identity_type: 'human' | 'admin' | 'service_account' | 'app' | 'contractor';
  status: 'active' | 'inactive' | 'suspended';
  department?: string;
  manager_email?: string;
  source_system: string;
  is_privileged: boolean;
  risk_score: number;
  last_active_at?: string;
}

export interface EffectiveGrant {
  id: string;
  application_id: string;
  application_name: string;
  entitlement_name?: string;
  role_name?: string;
  permission_type: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  is_direct: boolean;
  grant_date: string;
  status: string;
  justification?: string;
}

export interface ReviewCampaign {
  id: string;
  name: string;
  description?: string;
  scope: string;
  status: 'draft' | 'active' | 'completed' | 'overdue';
  start_date: string;
  due_date: string;
  total_items: number;
  reviewed_items: number;
}

export interface ReviewItem {
  grant_id: string;
  identity_id: string;
  username: string;
  full_name: string;
  department: string;
  is_privileged: boolean;
  application_name: string;
  entitlement_name: string;
  permission_type: string;
  risk_level: string;
  is_direct: boolean;
  grant_date: string;
  decision?: string;
  decision_comment?: string;
}

export interface RevocationRequest {
  id: string;
  grant_id: string;
  identity_id: string;
  status: 'requested' | 'pending_approval' | 'approved' | 'executing' | 'completed' | 'failed' | 'cancelled';
  target_system: string;
  error_message?: string;
  retry_count: number;
  executed_at?: string;
  created_at: string;
}

export interface RiskFinding {
  id: string;
  identity_id?: string;
  finding_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  rule_name: string;
  evidence: string;
  remediation: string;
  status: string;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  actor_name: string;
  action: string;
  target_entity: string;
  category: string;
  result: string;
  prev_hash: string;
  event_hash: string;
  metadata_json: string;
}

export interface DashboardStats {
  total_identities: number;
  active_identities: number;
  privileged_identities: number;
  total_grants: number;
  active_campaigns: number;
  overdue_reviews: number;
  pending_revocations: number;
  critical_findings: number;
  high_findings: number;
  audit_chain_valid: boolean;
}

export interface Connector {
  id: string;
  name: string;
  connector_type: string;
  status: string;
  sync_count: number;
  last_sync_at?: string;
}

export interface Policy {
  id: string;
  name: string;
  description?: string;
  rule_type: string;
  is_active: boolean;
}
