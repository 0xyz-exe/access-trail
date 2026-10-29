"""Access Review Campaigns and Decisions router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.access_review import ReviewCampaign, ReviewDecision
from backend.app.models.access_grant import AccessGrant
from backend.app.models.identity import Identity
from backend.app.models.permission import Entitlement, SystemRole, Application
from backend.app.models.user import User
from backend.app.schemas.review import CampaignCreate, CampaignOut, DecisionCreate, DecisionOut
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.review_service import ReviewService

router = APIRouter(prefix="/access-reviews", tags=["access-reviews"])

@router.get("/campaigns", response_model=list[CampaignOut])
def list_campaigns(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(ReviewCampaign).where(ReviewCampaign.tenant_id == current_user.tenant_id).order_by(ReviewCampaign.created_at.desc())
    return list(db.execute(stmt).scalars().all())

@router.post("/campaigns", response_model=CampaignOut)
def create_campaign(
    req: CampaignCreate,
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    return ReviewService.create_campaign(
        db=db,
        tenant_id=current_user.tenant_id,
        name=req.name,
        description=req.description,
        scope=req.scope,
        due_date=req.due_date,
        reviewer_id=req.reviewer_id,
        actor=current_user
    )

@router.get("/campaigns/{campaign_id}/items")
def get_campaign_review_items(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaign = db.execute(
        select(ReviewCampaign).where(ReviewCampaign.id == campaign_id, ReviewCampaign.tenant_id == current_user.tenant_id)
    ).scalars().first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found.")

    query = select(AccessGrant).where(AccessGrant.tenant_id == current_user.tenant_id, AccessGrant.status == "active")
    if campaign.scope == "privileged_only":
        query = query.join(Identity, Identity.id == AccessGrant.identity_id).where(Identity.is_privileged == True)

    grants = list(db.execute(query).scalars().all())

    # Get decisions already made in this campaign
    decisions = {
        d.grant_id: d
        for d in db.execute(
            select(ReviewDecision).where(ReviewDecision.campaign_id == campaign_id)
        ).scalars().all()
    }

    items = []
    for g in grants:
        idn = db.execute(select(Identity).where(Identity.id == g.identity_id)).scalars().first()
        app = db.execute(select(Application).where(Application.id == g.application_id)).scalars().first()
        ent = db.execute(select(Entitlement).where(Entitlement.id == g.entitlement_id)).scalars().first() if g.entitlement_id else None
        role = db.execute(select(SystemRole).where(SystemRole.id == g.role_id)).scalars().first() if g.role_id else None
        existing_dec = decisions.get(g.id)

        items.append({
            "grant_id": g.id,
            "identity_id": g.identity_id,
            "username": idn.username if idn else "Unknown",
            "full_name": idn.full_name if idn else "Unknown",
            "department": idn.department if idn else "",
            "is_privileged": idn.is_privileged if idn else False,
            "application_name": app.name if app else "Unknown",
            "entitlement_name": ent.permission_name if ent else (role.name if role else "Direct Access"),
            "permission_type": ent.permission_type if ent else "role",
            "risk_level": ent.risk_level if ent else "low",
            "is_direct": g.is_direct,
            "grant_date": g.grant_date.isoformat(),
            "decision": existing_dec.decision if existing_dec else None,
            "decision_comment": existing_dec.comments if existing_dec else None,
        })
    return {"campaign": CampaignOut.model_validate(campaign), "items": items}

@router.post("/decisions", response_model=DecisionOut)
def record_decision(
    req: DecisionCreate,
    current_user: User = Depends(require_role("platform_owner", "security_admin", "access_reviewer")),
    db: Session = Depends(get_db)
):
    return ReviewService.record_decision(
        db=db,
        tenant_id=current_user.tenant_id,
        campaign_id=req.campaign_id,
        identity_id=req.identity_id,
        grant_id=req.grant_id,
        decision=req.decision,
        comments=req.comments,
        actor=current_user
    )
