"""Test API endpoints via TestClient."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.cli.main import seed_demo

@pytest.fixture(scope="module", autouse=True)
def init_data():
    seed_demo()

client = TestClient(app)

def test_health_check():
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_auth_login():
    # Failure
    fail_res = client.post("/api/v1/auth/login", json={"email": "admin@acme.corp", "password": "WrongPassword"})
    assert fail_res.status_code == 401

    # Success
    succ_res = client.post("/api/v1/auth/login", json={"email": "admin@acme.corp", "password": "Password123!"})
    assert succ_res.status_code == 200
    data = succ_res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "platform_owner"

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # /auth/me
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@acme.corp"

    # /dashboard/stats
    dash_res = client.get("/api/v1/dashboard/stats", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_identities"] >= 7
    assert dash_data["audit_chain_valid"] is True

    # /identities
    idn_res = client.get("/api/v1/identities", headers=headers)
    assert idn_res.status_code == 200
    assert len(idn_res.json()) >= 7

    # /audit-logs/verify
    verify_res = client.get("/api/v1/audit-logs/verify", headers=headers)
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True

    # /reports/evidence-package
    ev_res = client.get("/api/v1/reports/evidence-package", headers=headers)
    assert ev_res.status_code == 200
    assert "integrity_verification" in ev_res.json()

def test_csv_formula_sanitization():
    from backend.app.core.security import sanitize_csv_cell
    assert sanitize_csv_cell("=SUM(1,2)") == "'=SUM(1,2)"
    assert sanitize_csv_cell("+cmd|'/C calc'!A0") == "'+cmd|'/C calc'!A0"
    assert sanitize_csv_cell("-100") == "'-100"
    assert sanitize_csv_cell("@something") == "'@something"
    assert sanitize_csv_cell("normal text") == "normal text"
