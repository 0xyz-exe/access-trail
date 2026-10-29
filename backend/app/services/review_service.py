"""Access review and certification campaign service."""
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.app.models.access_review import ReviewCampaign, ReviewDecision
from backend.app.models.access_grant import AccessGrant
from backend.app.models.identity import Identity
from backend.app.models.revocation import RevocationRequest
from backend.app.models.user import User
from backend.app.services.audit_service import AuditService

class ReviewService:
    @staticmethod
    def create_campaign(
        db: Session,
        tenant_id: str,
        name: str,
        description: str | None,
        scope: str,
        due_date: datetime,
        reviewer_id: str | None,
        actor: User
    ) -> ReviewCampaign:
        # Determine total eligible grants in scope
        query = select(func.count(AccessGrant.id)).where(
            AccessGrant.tenant_id == tenant_id,
            AccessGrant.status == "active"
        )
        if scope == "privileged_only":
            query = query.join(Identity, Identity.id == AccessGrant.identity_id).where(Identity.is_privileged == True)

        total_count = db.execute(query).scalar() or 0

        campaign = ReviewCampaign(
            tenant_id=tenant_id,
            name=name,
            description=description,
            scope=scope,
            reviewer_id=reviewer_id,
            due_date=due_date,
            total_items=total_count,
            reviewed_items=0,
            status="active" if total_count > 0 else "completed"
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            action="review.campaign_create",
            target_entity=campaign.id,
            category="access_review",
            metadata={"name": name, "scope": scope, "total_items": total_count}
        )
        return campaign

    @staticmethod
    def record_decision(
        db: Session,
        tenant_id: str,
        campaign_id: str,
        identity_id: str,
        grant_id: str,
        decision: str,
        comments: str | None,
        actor: User
    ) -> ReviewDecision:
        # 1. Verify campaign exists
        campaign = db.execute(
            select(ReviewCampaign).where(ReviewCampaign.id == campaign_id, ReviewCampaign.tenant_id == tenant_id)
        ).scalars().first()
        if not campaign:
            raise HTTPException(status_code=404, detail="Review campaign not found.")

        # 2. Separation of Duties check: reviewer cannot self-approve own access
        identity = db.execute(
            select(Identity).where(Identity.id == identity_id, Identity.tenant_id == tenant_id)
        ).scalars().first()
        if identity and identity.email == actor.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Separation of Duties violation: Reviewers cannot approve or certify their own access."
            )

        # 3. Create review decision
        rev_decision = ReviewDecision(
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            reviewer_id=actor.id,
            identity_id=identity_id,
            grant_id=grant_id,
            decision=decision,
            comments=comments
        )
        db.add(rev_decision)

        # 4. If decision is revoke, generate RevocationRequest
        if decision == "revoke":
            rev_req = RevocationRequest(
                tenant_id=tenant_id,
                decision_id=rev_decision.id,
                grant_id=grant_id,
                identity_id=identity_id,
                status="requested",
                target_system="connector_mock",
                requires_dual_approval=False
            )
            db.add(rev_req)

        # 5. Update campaign progress
        campaign.reviewed_items += 1
        if campaign.reviewed_items >= campaign.total_items:
            campaign.status = "completed"

        db.commit()
        db.refresh(rev_decision)

        AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            action=f"review.decision_{decision}",
            target_entity=grant_id,
            category="access_review",
            metadata={"campaign_id": campaign_id, "identity_id": identity_id, "decision": decision}
        )
        return rev_decision
