"""Connector and Notification models."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.models.base import Base, TenantScopedMixin, utc_now

class ConnectorConfig(Base, TenantScopedMixin):
    __tablename__ = "connector_configs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"con_{uuid.uuid4().hex[:12]}")
    name: Mapped[str] = mapped_column(String(128), index=True)
    connector_type: Mapped[str] = mapped_column(String(64)) # csv, mock_idp, mock_entitlements, oidc
    status: Mapped[str] = mapped_column(String(32), default="healthy") # healthy, error, sync_running
    sync_count: Mapped[int] = mapped_column(Integer, default=0)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config_json: Mapped[str] = mapped_column(Text, default="{}")

class Notification(Base, TenantScopedMixin):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"not_{uuid.uuid4().hex[:12]}")
    user_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True) # None = tenant-wide
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(32), default="info") # info, warning, critical
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
