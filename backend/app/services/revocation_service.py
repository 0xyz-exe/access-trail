"""Revocation workflow execution and state machine service."""
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.revocation import RevocationRequest
from backend.app.models.access_grant import AccessGrant
from backend.app.models.user import User
from backend.app.services.audit_service import AuditService

class RevocationService:
    @staticmethod
    def list_requests(db: Session, tenant_id: str, status_filter: str | None = None) -> list[RevocationRequest]:
        stmt = select(RevocationRequest).where(RevocationRequest.tenant_id == tenant_id)
        if status_filter:
            stmt = stmt.where(RevocationRequest.status == status_filter)
        stmt = stmt.order_by(RevocationRequest.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def approve_request(db: Session, tenant_id: str, request_id: str, actor: User) -> RevocationRequest:
        rev_req = db.execute(
            select(RevocationRequest).where(RevocationRequest.id == request_id, RevocationRequest.tenant_id == tenant_id)
        ).scalars().first()
        if not rev_req:
            raise HTTPException(status_code=404, detail="Revocation request not found.")

        rev_req.status = "approved"
        rev_req.approved_by = actor.id
        db.commit()
        db.refresh(rev_req)

        AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            action="revocation.approved",
            target_entity=request_id,
            category="revocation",
            metadata={"status": rev_req.status}
        )
        return rev_req

    @staticmethod
    def execute_revocation(db: Session, tenant_id: str, request_id: str, actor: User) -> RevocationRequest:
        """Execute revocation against connector/target system idempotently."""
        rev_req = db.execute(
            select(RevocationRequest).where(RevocationRequest.id == request_id, RevocationRequest.tenant_id == tenant_id)
        ).scalars().first()
        if not rev_req:
            raise HTTPException(status_code=404, detail="Revocation request not found.")

        if rev_req.status == "completed":
            return rev_req # Idempotent no-op

        # Fetch underlying access grant
        grant = db.execute(
            select(AccessGrant).where(AccessGrant.id == rev_req.grant_id, AccessGrant.tenant_id == tenant_id)
        ).scalars().first()

        try:
            # Simulate connector API invocation to revoke external permission
            # Update grant status
            if grant:
                grant.status = "revoked"

            rev_req.status = "completed"
            rev_req.executed_at = datetime.now(timezone.utc)
            rev_req.error_message = None
            db.commit()
            db.refresh(rev_req)

            AuditService.log_event(
                db=db,
                tenant_id=tenant_id,
                actor_id=actor.id,
                actor_name=actor.full_name,
                action="revocation.executed",
                target_entity=request_id,
                category="revocation",
                result="success",
                metadata={"grant_id": rev_req.grant_id, "target_system": rev_req.target_system}
            )
            return rev_req

        except Exception as exc:
            rev_req.status = "failed"
            rev_req.retry_count += 1
            rev_req.error_message = str(exc)
            db.commit()
            db.refresh(rev_req)

            AuditService.log_event(
                db=db,
                tenant_id=tenant_id,
                actor_id=actor.id,
                actor_name=actor.full_name,
                action="revocation.execution_failed",
                target_entity=request_id,
                category="revocation",
                result="failure",
                metadata={"error": str(exc)}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Revocation failed: {exc}"
            )
