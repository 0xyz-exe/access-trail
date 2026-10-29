"""Dashboard analytics router with live SQL aggregations."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.identity import Identity
from backend.app.models.access_grant import AccessGrant
from backend.app.models.access_review import ReviewCampaign
from backend.app.models.revocation import RevocationRequest
from backend.app.models.risk_finding import RiskFinding
from backend.app.models.user import User
from backend.app.schemas.review import DashboardStats
from backend.app.services.auth_service import get_current_user
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_id = current_user.tenant_id

    total_idn = db.execute(select(func.count(Identity.id)).where(Identity.tenant_id == tenant_id)).scalar() or 0
    active_idn = db.execute(select(func.count(Identity.id)).where(Identity.tenant_id == tenant_id, Identity.status == "active")).scalar() or 0
    priv_idn = db.execute(select(func.count(Identity.id)).where(Identity.tenant_id == tenant_id, Identity.is_privileged == True)).scalar() or 0

    total_grants = db.execute(select(func.count(AccessGrant.id)).where(AccessGrant.tenant_id == tenant_id, AccessGrant.status == "active")).scalar() or 0
    active_camp = db.execute(select(func.count(ReviewCampaign.id)).where(ReviewCampaign.tenant_id == tenant_id, ReviewCampaign.status == "active")).scalar() or 0
    overdue_camp = db.execute(select(func.count(ReviewCampaign.id)).where(ReviewCampaign.tenant_id == tenant_id, ReviewCampaign.status == "overdue")).scalar() or 0

    pending_rev = db.execute(
        select(func.count(RevocationRequest.id)).where(
            RevocationRequest.tenant_id == tenant_id,
            RevocationRequest.status.in_(["requested", "pending_approval", "failed"])
        )
    ).scalar() or 0

    crit_findings = db.execute(select(func.count(RiskFinding.id)).where(RiskFinding.tenant_id == tenant_id, RiskFinding.severity == "critical", RiskFinding.status == "open")).scalar() or 0
    high_findings = db.execute(select(func.count(RiskFinding.id)).where(RiskFinding.tenant_id == tenant_id, RiskFinding.severity == "high", RiskFinding.status == "open")).scalar() or 0

    chain_status = AuditService.verify_chain(db, tenant_id)

    return DashboardStats(
        total_identities=total_idn,
        active_identities=active_idn,
        privileged_identities=priv_idn,
        total_grants=total_grants,
        active_campaigns=active_camp,
        overdue_reviews=overdue_camp,
        pending_revocations=pending_rev,
        critical_findings=crit_findings,
        high_findings=high_findings,
        audit_chain_valid=chain_status.get("is_valid", True)
    )
