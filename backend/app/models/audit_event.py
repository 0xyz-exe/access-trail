"""Tamper-evident audit event model with cryptographic hash chaining."""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TenantScopedMixin, utc_now

class AuditEvent(Base, TenantScopedMixin):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    actor_id: Mapped[str] = mapped_column(String(64), index=True)
    actor_name: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64), index=True) # auth.login, identity.create, review.decide, revoke.execute, policy.update, etc.
    target_entity: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str] = mapped_column(String(64), default="security", index=True) # security, access_review, revocation, administration
    result: Mapped[str] = mapped_column(String(32), default="success") # success, failure, denied
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")

    # Cryptographic integrity chain
    prev_hash: Mapped[str] = mapped_column(String(64)) # "0" for genesis event
    event_hash: Mapped[str] = mapped_column(String(64), index=True) # sha256(prev_hash + canonical_json)
