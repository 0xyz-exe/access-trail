"""Risk findings router."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.risk_finding import RiskFinding
from backend.app.models.user import User
from backend.app.schemas.review import RiskFindingOut
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.risk_engine import RiskEngine

router = APIRouter(prefix="/findings", tags=["findings"])

@router.get("", response_model=list[RiskFindingOut])
def get_findings(
    severity: str | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stmt = select(RiskFinding).where(RiskFinding.tenant_id == current_user.tenant_id)
    if severity:
        stmt = stmt.where(RiskFinding.severity == severity)
    if status:
        stmt = stmt.where(RiskFinding.status == status)
    stmt = stmt.order_by(RiskFinding.created_at.desc())
    return list(db.execute(stmt).scalars().all())

@router.post("/scan", response_model=list[RiskFindingOut])
def run_risk_scan(
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    return RiskEngine.evaluate_risks(db, current_user.tenant_id)
