"""Review, Revocation, Risk, and Audit schemas."""
from datetime import datetime
from pydantic import BaseModel

class CampaignCreate(BaseModel):
    name: str
    description: str | None = None
    scope: str = "all"
    target_application_id: str | None = None
    reviewer_id: str | None = None
    due_date: datetime

class CampaignOut(CampaignCreate):
    id: str
    tenant_id: str
    status: str
    start_date: datetime
    total_items: int
    reviewed_items: int
    created_at: datetime

    model_config = {"from_attributes": True}

class DecisionCreate(BaseModel):
    campaign_id: str
    identity_id: str
    grant_id: str
    decision: str # approve, revoke, request_info, escalate
    comments: str | None = None

class DecisionOut(DecisionCreate):
    id: str
    tenant_id: str
    reviewer_id: str
    decided_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}

class RevocationRequestOut(BaseModel):
    id: str
    tenant_id: str
    decision_id: str | None = None
    grant_id: str
    identity_id: str
    status: str
    target_system: str
    requires_dual_approval: bool
    approved_by: str | None = None
    error_message: str | None = None
    retry_count: int
    executed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

class RiskFindingOut(BaseModel):
    id: str
    tenant_id: str
    identity_id: str | None = None
    finding_type: str
    severity: str
    rule_name: str
    evidence: str
    remediation: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

class AuditEventOut(BaseModel):
    id: str
    tenant_id: str
    timestamp: datetime
    actor_id: str
    actor_name: str
    action: str
    target_entity: str
    category: str
    result: str
    metadata_json: str
    prev_hash: str
    event_hash: str

    model_config = {"from_attributes": True}

class AuditVerifyResponse(BaseModel):
    total_events: int
    is_valid: bool
    broken_event_id: str | None = None
    details: str

class DashboardStats(BaseModel):
    total_identities: int
    active_identities: int
    privileged_identities: int
    total_grants: int
    active_campaigns: int
    overdue_reviews: int
    pending_revocations: int
    critical_findings: int
    high_findings: int
    audit_chain_valid: bool
