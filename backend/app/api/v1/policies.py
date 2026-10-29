"""Access policies router."""
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.policy import AccessPolicy
from backend.app.models.user import User
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/policies", tags=["policies"])

class PolicyCreate(BaseModel):
    name: str
    description: str | None = None
    rule_type: str
    parameters_json: str = "{}"
    is_active: bool = True

class PolicyOut(PolicyCreate):
    id: str
    tenant_id: str

    model_config = {"from_attributes": True}

@router.get("", response_model=list[PolicyOut])
def get_policies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(AccessPolicy).where(AccessPolicy.tenant_id == current_user.tenant_id)
    return list(db.execute(stmt).scalars().all())

@router.post("", response_model=PolicyOut)
def create_policy(
    req: PolicyCreate,
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    pol = AccessPolicy(tenant_id=current_user.tenant_id, **req.model_dump())
    db.add(pol)
    db.commit()
    db.refresh(pol)

    AuditService.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        action="policy.create",
        target_entity=pol.id,
        category="security",
        metadata={"name": pol.name, "rule_type": pol.rule_type}
    )
    return pol
