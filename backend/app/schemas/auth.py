"""Auth and User schemas."""
from datetime import datetime
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: str = "standard_user"
    tenant_id: str

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
