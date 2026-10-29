"""Test Access Review campaign, Separation of Duties, and Revocation workflow."""
from datetime import datetime, timezone, timedelta
import pytest
from fastapi import HTTPException
from backend.app.db.session import SessionLocal, init_db
from backend.app.models.user import User
from backend.app.models.identity import Identity
from backend.app.models.permission import Application, Entitlement
from backend.app.models.access_grant import AccessGrant
from backend.app.models.revocation import RevocationRequest
from backend.app.services.review_service import ReviewService
from backend.app.services.revocation_service import RevocationService

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_access_review_workflow_and_sod():
    db = SessionLocal()
    tenant = "test_review_tenant"
    now = datetime.now(timezone.utc)

    # Clean previous tenant test records
    db.query(AccessGrant).filter(AccessGrant.tenant_id == tenant).delete()
    db.query(Identity).filter(Identity.tenant_id == tenant).delete()
    db.query(User).filter(User.tenant_id == tenant).delete()
    db.query(RevocationRequest).filter(RevocationRequest.tenant_id == tenant).delete()
    db.commit()

    # Reviewer user
    reviewer = User(
        tenant_id=tenant,
        email="reviewer@corp.net",
        full_name="Reviewer Lead",
        role="access_reviewer",
        password_hash="fake"
    )
    db.add(reviewer)
    db.commit()

    # Identity 1: regular employee
    idn_user = Identity(
        tenant_id=tenant,
        username="john.doe",
        email="john.doe@corp.net",
        full_name="John Doe",
        identity_type="human",
        is_privileged=True
    )
    # Identity 2: reviewer's own identity (same email)
    idn_self = Identity(
        tenant_id=tenant,
        username="reviewer.lead",
        email="reviewer@corp.net",
        full_name="Reviewer Lead",
        identity_type="human",
        is_privileged=True
    )
    db.add_all([idn_user, idn_self])
    db.commit()

    # Application & Entitlement
    app = Application(tenant_id=tenant, name="Test App")
    db.add(app)
    db.commit()

    ent = Entitlement(tenant_id=tenant, application_id=app.id, permission_name="admin", risk_level="high")
    db.add(ent)
    db.commit()

    # Grants
    gnt_user = AccessGrant(tenant_id=tenant, identity_id=idn_user.id, application_id=app.id, entitlement_id=ent.id, status="active")
    gnt_self = AccessGrant(tenant_id=tenant, identity_id=idn_self.id, application_id=app.id, entitlement_id=ent.id, status="active")
    db.add_all([gnt_user, gnt_self])
    db.commit()

    # Create campaign
    camp = ReviewService.create_campaign(
        db=db,
        tenant_id=tenant,
        name="Security Audit Campaign",
        description="Verify privileged access",
        scope="privileged_only",
        due_date=now + timedelta(days=7),
        reviewer_id=reviewer.id,
        actor=reviewer
    )
    assert camp.total_items == 2
    assert camp.status == "active"

    # Separation of Duties check: reviewer trying to approve own access must raise HTTPException(400)
    with pytest.raises(HTTPException) as exc_info:
        ReviewService.record_decision(
            db=db,
            tenant_id=tenant,
            campaign_id=camp.id,
            identity_id=idn_self.id,
            grant_id=gnt_self.id,
            decision="approve",
            comments="Self approval attempt",
            actor=reviewer
        )
    assert exc_info.value.status_code == 400
    assert "Separation of Duties" in exc_info.value.detail

    # Now review john.doe with "revoke"
    dec = ReviewService.record_decision(
        db=db,
        tenant_id=tenant,
        campaign_id=camp.id,
        identity_id=idn_user.id,
        grant_id=gnt_user.id,
        decision="revoke",
        comments="Revoking excess privilege",
        actor=reviewer
    )
    assert dec.decision == "revoke"

    # Verify RevocationRequest automatically created
    rev_reqs = RevocationService.list_requests(db, tenant)
    assert len(rev_reqs) == 1
    req = rev_reqs[0]
    assert req.status == "requested"
    assert req.grant_id == gnt_user.id

    # Execute revocation
    executed_req = RevocationService.execute_revocation(db, tenant, req.id, reviewer)
    assert executed_req.status == "completed"

    # Verify grant status is updated to 'revoked'
    db.refresh(gnt_user)
    assert gnt_user.status == "revoked"

    # Idempotent re-execution
    re_executed = RevocationService.execute_revocation(db, tenant, req.id, reviewer)
    assert re_executed.status == "completed"

    db.close()
