"""Permissions, Applications, Entitlements, and Access Grants router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.permission import Application, Resource, SystemRole, Entitlement
from backend.app.models.access_grant import AccessGrant
from backend.app.models.user import User
from backend.app.schemas.permission import (
    ApplicationCreate, ApplicationOut, EntitlementCreate, EntitlementOut,
    AccessGrantCreate, AccessGrantOut
)
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/permissions", tags=["permissions"])

@router.get("/applications", response_model=list[ApplicationOut])
def get_applications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Application).where(Application.tenant_id == current_user.tenant_id)
    return list(db.execute(stmt).scalars().all())

@router.post("/applications", response_model=ApplicationOut)
def create_application(
    req: ApplicationCreate,
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    app = Application(tenant_id=current_user.tenant_id, **req.model_dump())
    db.add(app)
    db.commit()
    db.refresh(app)
    return app

@router.get("/entitlements", response_model=list[EntitlementOut])
def get_entitlements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Entitlement).where(Entitlement.tenant_id == current_user.tenant_id)
    return list(db.execute(stmt).scalars().all())

@router.post("/entitlements", response_model=EntitlementOut)
def create_entitlement(
    req: EntitlementCreate,
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    ent = Entitlement(tenant_id=current_user.tenant_id, **req.model_dump())
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent

@router.get("/grants", response_model=list[AccessGrantOut])
def get_grants(
    identity_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stmt = select(AccessGrant).where(AccessGrant.tenant_id == current_user.tenant_id)
    if identity_id:
        stmt = stmt.where(AccessGrant.identity_id == identity_id)
    stmt = stmt.order_by(AccessGrant.grant_date.desc())
    return list(db.execute(stmt).scalars().all())

@router.post("/grants", response_model=AccessGrantOut)
def create_grant(
    req: AccessGrantCreate,
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    grant = AccessGrant(
        tenant_id=current_user.tenant_id,
        granted_by=current_user.full_name,
        **req.model_dump()
    )
    db.add(grant)
    db.commit()
    db.refresh(grant)

    AuditService.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        action="grant.create",
        target_entity=grant.id,
        category="administration",
        metadata={"identity_id": req.identity_id, "app_id": req.application_id}
    )
    return grant
