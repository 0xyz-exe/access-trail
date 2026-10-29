"""Identity and Group schemas."""
from datetime import datetime
from pydantic import BaseModel

class IdentityBase(BaseModel):
    username: str
    email: str | None = None
    full_name: str
    identity_type: str = "human" # human, admin, service_account, app, contractor
    status: str = "active" # active, inactive, suspended
    department: str | None = None
    manager_email: str | None = None
    source_system: str = "local"
    external_id: str | None = None
    risk_score: int = 0
    is_privileged: bool = False

class IdentityCreate(IdentityBase):
    pass

class IdentityUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    identity_type: str | None = None
    status: str | None = None
    department: str | None = None
    manager_email: str | None = None
    risk_score: int | None = None
    is_privileged: bool | None = None

class IdentityOut(IdentityBase):
    id: str
    tenant_id: str
    last_active_at: datetime | None = None
    last_sync_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class IdentityGroupOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str | None = None
    source_system: str
    created_at: datetime

    model_config = {"from_attributes": True}
