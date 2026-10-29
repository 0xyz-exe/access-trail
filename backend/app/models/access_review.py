"""Access Review Campaign and Decision models."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TenantScopedMixin, utc_now

class ReviewCampaign(Base, TenantScopedMixin):
    __tablename__ = "review_campaigns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"cmp_{uuid.uuid4().hex[:12]}")
    name: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str] = mapped_column(String(64), default="all") # all, privileged_only, application, department
    target_application_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="active", index=True) # draft, active, completed, overdue
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    reviewed_items: Mapped[int] = mapped_column(Integer, default=0)

class ReviewDecision(Base, TenantScopedMixin):
    __tablename__ = "review_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"dec_{uuid.uuid4().hex[:12]}")
    campaign_id: Mapped[str] = mapped_column(String(64), ForeignKey("review_campaigns.id", ondelete="CASCADE"), index=True)
    reviewer_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    identity_id: Mapped[str] = mapped_column(String(64), ForeignKey("identities.id", ondelete="CASCADE"), index=True)
    grant_id: Mapped[str] = mapped_column(String(64), ForeignKey("access_grants.id", ondelete="CASCADE"), index=True)

    decision: Mapped[str] = mapped_column(String(32), index=True) # approve, revoke, request_info, escalate
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
