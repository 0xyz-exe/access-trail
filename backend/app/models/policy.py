"""Access policy models."""
import uuid
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TenantScopedMixin

class AccessPolicy(Base, TenantScopedMixin):
    __tablename__ = "access_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"pol_{uuid.uuid4().hex[:12]}")
    name: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_type: Mapped[str] = mapped_column(String(64), index=True) # periodic_review, admin_justification_required, max_grant_duration, sod_no_self_approval
    parameters_json: Mapped[str] = mapped_column(Text, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
