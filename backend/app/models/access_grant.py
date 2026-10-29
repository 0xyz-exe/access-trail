"""Access grant model capturing identity-entitlement associations and provenance."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TenantScopedMixin, utc_now

class AccessGrant(Base, TenantScopedMixin):
    __tablename__ = "access_grants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"gnt_{uuid.uuid4().hex[:12]}")
    identity_id: Mapped[str] = mapped_column(String(64), ForeignKey("identities.id", ondelete="CASCADE"), index=True)
    application_id: Mapped[str] = mapped_column(String(64), ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    entitlement_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("entitlements.id", ondelete="CASCADE"), nullable=True)
    role_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("system_roles.id", ondelete="CASCADE"), nullable=True)

    is_direct: Mapped[bool] = mapped_column(Boolean, default=True) # direct grant vs inherited via group/role
    granted_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    grant_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    business_justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True) # active, revoked, expired
