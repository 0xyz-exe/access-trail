"""Permission Revocation workflow model."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TenantScopedMixin

class RevocationRequest(Base, TenantScopedMixin):
    __tablename__ = "revocation_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"rvk_{uuid.uuid4().hex[:12]}")
    decision_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("review_decisions.id", ondelete="SET NULL"), nullable=True)
    grant_id: Mapped[str] = mapped_column(String(64), ForeignKey("access_grants.id", ondelete="CASCADE"), index=True)
    identity_id: Mapped[str] = mapped_column(String(64), ForeignKey("identities.id", ondelete="CASCADE"), index=True)

    status: Mapped[str] = mapped_column(String(32), default="requested", index=True) # requested, pending_approval, approved, executing, completed, failed, cancelled
    target_system: Mapped[str] = mapped_column(String(64), default="mock_connector")
    requires_dual_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
