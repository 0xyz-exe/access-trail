"""Audit events and integrity verification router."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.audit_event import AuditEvent
from backend.app.models.user import User
from backend.app.schemas.review import AuditEventOut, AuditVerifyResponse
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])

@router.get("", response_model=list[AuditEventOut])
def get_audit_events(
    category: str | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_role("platform_owner", "security_admin", "auditor")),
    db: Session = Depends(get_db)
):
    stmt = select(AuditEvent).where(AuditEvent.tenant_id == current_user.tenant_id)
    if category:
        stmt = stmt.where(AuditEvent.category == category)
    if action:
        stmt = stmt.where(AuditEvent.action == action)
    stmt = stmt.order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc()).offset(offset).limit(limit)
    return list(db.execute(stmt).scalars().all())

@router.get("/verify", response_model=AuditVerifyResponse)
def verify_audit_integrity(
    current_user: User = Depends(require_role("platform_owner", "security_admin", "auditor")),
    db: Session = Depends(get_db)
):
    """Cryptographically verify the tamper-evident hash chain for this tenant."""
    result = AuditService.verify_chain(db, current_user.tenant_id)
    return AuditVerifyResponse(**result)
