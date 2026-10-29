"""Identity and Group models."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TenantScopedMixin

class Identity(Base, TenantScopedMixin):
    __tablename__ = "identities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"idn_{uuid.uuid4().hex[:12]}")
    username: Mapped[str] = mapped_column(String(128), index=True)
    email: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(128))
    identity_type: Mapped[str] = mapped_column(String(32), index=True) # human, admin, service_account, app, contractor
    status: Mapped[str] = mapped_column(String(32), default="active", index=True) # active, inactive, suspended
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    manager_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_system: Mapped[str] = mapped_column(String(64), default="local") # local, okta, azure_ad, google_workspace, csv
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0) # 0 - 100
    is_privileged: Mapped[bool] = mapped_column(Boolean, default=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class IdentityGroup(Base, TenantScopedMixin):
    __tablename__ = "identity_groups"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"grp_{uuid.uuid4().hex[:12]}")
    name: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_system: Mapped[str] = mapped_column(String(64), default="local")

class GroupMembership(Base, TenantScopedMixin):
    __tablename__ = "group_memberships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"gmb_{uuid.uuid4().hex[:12]}")
    group_id: Mapped[str] = mapped_column(String(64), ForeignKey("identity_groups.id", ondelete="CASCADE"), index=True)
    identity_id: Mapped[str] = mapped_column(String(64), ForeignKey("identities.id", ondelete="CASCADE"), index=True)
