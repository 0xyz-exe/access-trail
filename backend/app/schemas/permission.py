"""Permission, Role, Application, and Grant schemas."""
from datetime import datetime
from pydantic import BaseModel

class ApplicationCreate(BaseModel):
    name: str
    description: str | None = None
    app_type: str = "saas"
    is_sensitive: bool = False

class ApplicationOut(ApplicationCreate):
    id: str
    tenant_id: str
    created_at: datetime

    model_config = {"from_attributes": True}

class ResourceOut(BaseModel):
    id: str
    tenant_id: str
    application_id: str
    name: str
    resource_type: str
    is_sensitive: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class SystemRoleOut(BaseModel):
    id: str
    tenant_id: str
    application_id: str
    name: str
    description: str | None = None
    is_privileged: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class EntitlementCreate(BaseModel):
    application_id: str
    resource_id: str | None = None
    permission_name: str
    permission_type: str = "custom"
    risk_level: str = "low"

class EntitlementOut(EntitlementCreate):
    id: str
    tenant_id: str
    created_at: datetime

    model_config = {"from_attributes": True}

class AccessGrantCreate(BaseModel):
    identity_id: str
    application_id: str
    entitlement_id: str | None = None
    role_id: str | None = None
    is_direct: bool = True
    granted_by: str | None = None
    business_justification: str | None = None
    approval_reference: str | None = None
    expires_at: datetime | None = None

class AccessGrantOut(AccessGrantCreate):
    id: str
    tenant_id: str
    grant_date: datetime
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
