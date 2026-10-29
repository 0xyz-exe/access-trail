"""User model for tenant users and authentication."""
import uuid
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TenantScopedMixin

class User(Base, TenantScopedMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"usr_{uuid.uuid4().hex[:12]}")
    email: Mapped[str] = mapped_column(String(255), index=True)
    full_name: Mapped[str] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(32),
        default="standard_user"
    ) # platform_owner, security_admin, access_reviewer, auditor, read_only_analyst, standard_user
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    session_token: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
