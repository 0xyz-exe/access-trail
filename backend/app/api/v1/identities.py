"""Identities router."""
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.identity import Identity
from backend.app.models.access_grant import AccessGrant
from backend.app.models.permission import Entitlement, SystemRole, Application
from backend.app.models.user import User
from backend.app.schemas.identity import IdentityCreate, IdentityOut, IdentityUpdate
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.identity_service import IdentityService
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/identities", tags=["identities"])

@router.get("", response_model=list[IdentityOut])
def get_identities(
    search: str | None = None,
    identity_type: str | None = None,
    status: str | None = None,
    department: str | None = None,
    is_privileged: bool | None = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return IdentityService.list_identities(
        db=db,
        tenant_id=current_user.tenant_id,
        search=search,
        identity_type=identity_type,
        status=status,
        department=department,
        is_privileged=is_privileged,
        limit=limit,
        offset=offset
    )

@router.get("/export/csv")
def export_identities_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    csv_data = IdentityService.export_csv(db, current_user.tenant_id)
    AuditService.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        action="identity.export_csv",
        target_entity="identities_csv",
        category="administration"
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="identities_export.csv"'}
    )

@router.post("/import/csv")
async def import_identities_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    content = (await file.read()).decode("utf-8")
    result = IdentityService.import_csv(
        db=db,
        tenant_id=current_user.tenant_id,
        csv_content=content,
        actor_id=current_user.id,
        actor_name=current_user.full_name
    )
    return result

@router.post("", response_model=IdentityOut)
def create_identity(
    req: IdentityCreate,
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    existing = db.execute(
        select(Identity).where(Identity.tenant_id == current_user.tenant_id, Identity.username == req.username)
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Identity with this username already exists.")

    identity = Identity(
        tenant_id=current_user.tenant_id,
        **req.model_dump()
    )
    db.add(identity)
    db.commit()
    db.refresh(identity)

    AuditService.log_event(
        db=db,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        actor_name=current_user.full_name,
        action="identity.create",
        target_entity=identity.id,
        category="administration",
        metadata={"username": identity.username, "type": identity.identity_type}
    )
    return identity

@router.get("/{identity_id}")
def get_identity_details(
    identity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    idn = db.execute(
        select(Identity).where(Identity.id == identity_id, Identity.tenant_id == current_user.tenant_id)
    ).scalars().first()
    if not idn:
        raise HTTPException(status_code=404, detail="Identity not found.")

    # Fetch effective permissions / grants with details
    grants = list(db.execute(
        select(AccessGrant).where(AccessGrant.identity_id == identity_id, AccessGrant.tenant_id == current_user.tenant_id)
    ).scalars().all())

    grant_details = []
    for g in grants:
        app = db.execute(select(Application).where(Application.id == g.application_id)).scalars().first()
        ent = db.execute(select(Entitlement).where(Entitlement.id == g.entitlement_id)).scalars().first() if g.entitlement_id else None
        role = db.execute(select(SystemRole).where(SystemRole.id == g.role_id)).scalars().first() if g.role_id else None

        grant_details.append({
            "id": g.id,
            "application_id": g.application_id,
            "application_name": app.name if app else "Unknown",
            "entitlement_name": ent.permission_name if ent else None,
            "role_name": role.name if role else None,
            "permission_type": ent.permission_type if ent else "role",
            "risk_level": ent.risk_level if ent else ("critical" if role and role.is_privileged else "low"),
            "is_direct": g.is_direct,
            "grant_date": g.grant_date.isoformat(),
            "expires_at": g.expires_at.isoformat() if g.expires_at else None,
            "status": g.status,
            "justification": g.business_justification,
        })

    return {
        "identity": IdentityOut.model_validate(idn),
        "grants": grant_details
    }
