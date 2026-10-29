"""Test cryptographic audit chain and tamper-evident detection."""
import pytest
from sqlalchemy import select
from backend.app.db.session import SessionLocal, init_db
from backend.app.models.audit_event import AuditEvent
from backend.app.services.audit_service import AuditService

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_audit_hash_chain_integrity():
    db = SessionLocal()
    tenant_id = "test_audit_tenant_1"

    # Clean existing
    db.query(AuditEvent).filter(AuditEvent.tenant_id == tenant_id).delete()
    db.commit()

    # Log 3 events
    e1 = AuditService.log_event(db, tenant_id, "u1", "User One", "login", "auth")
    e2 = AuditService.log_event(db, tenant_id, "u1", "User One", "view", "identity")
    e3 = AuditService.log_event(db, tenant_id, "u2", "User Two", "revoke", "grant")

    # Initial verification must pass
    result = AuditService.verify_chain(db, tenant_id)
    assert result["is_valid"] is True
    assert result["total_events"] == 3
    assert result["broken_event_id"] is None

    # Tampering test: artificially modify event 2 payload directly in DB
    e2.metadata_json = '{"tampered": true}'
    db.commit()

    # Re-verify: must catch tampering at e2
    tampered_result = AuditService.verify_chain(db, tenant_id)
    assert tampered_result["is_valid"] is False
    assert tampered_result["broken_event_id"] == e2.id
    assert "Tampering detected" in tampered_result["details"]

    db.close()
