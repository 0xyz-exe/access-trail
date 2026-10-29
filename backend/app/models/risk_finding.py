"""Risk findings and excessive privilege models."""
import uuid
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TenantScopedMixin

class RiskFinding(Base, TenantScopedMixin):
    __tablename__ = "risk_findings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"fnd_{uuid.uuid4().hex[:12]}")
    identity_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("identities.id", ondelete="CASCADE"), nullable=True, index=True)
    finding_type: Mapped[str] = mapped_column(String(64), index=True) # orphaned_identity, dormant_privileged, direct_admin, overdue_review, expired_grant, unassigned_service_account
    severity: Mapped[str] = mapped_column(String(32), index=True) # low, medium, high, critical
    rule_name: Mapped[str] = mapped_column(String(128))
    evidence: Mapped[str] = mapped_column(Text)
    remediation: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True) # open, resolved, suppressed
