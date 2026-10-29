"""Test authentication, roles, and tenant isolation."""
import pytest
from backend.app.core.security import hash_password, verify_password
from backend.app.db.session import SessionLocal, init_db
from backend.app.models.user import User
from backend.app.models.identity import Identity
from backend.app.services.auth_service import AuthService
from backend.app.services.identity_service import IdentityService

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_password_hashing():
    pwd = "SecurePassword123!"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False

def test_tenant_isolation():
    db = SessionLocal()
    tenant_a = "tenant_alpha"
    tenant_b = "tenant_beta"

    # Clean
    db.query(Identity).filter(Identity.tenant_id.in_([tenant_a, tenant_b])).delete()
    db.commit()

    # Create identity in Tenant A
    id_a = Identity(tenant_id=tenant_a, username="alice.alpha", full_name="Alice Alpha", identity_type="human")
    db.add(id_a)
    # Create identity in Tenant B
    id_b = Identity(tenant_id=tenant_b, username="bob.beta", full_name="Bob Beta", identity_type="human")
    db.add(id_b)
    db.commit()

    # Query for Tenant A must never return Tenant B
    list_a = IdentityService.list_identities(db, tenant_a)
    assert len(list_a) == 1
    assert list_a[0].username == "alice.alpha"

    # Query for Tenant B must never return Tenant A
    list_b = IdentityService.list_identities(db, tenant_b)
    assert len(list_b) == 1
    assert list_b[0].username == "bob.beta"

    db.close()
