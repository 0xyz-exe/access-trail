"""Permission, Role, Application, and Resource models."""
import uuid
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, TenantScopedMixin

class Application(Base, TenantScopedMixin):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"app_{uuid.uuid4().hex[:12]}")
    name: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    app_type: Mapped[str] = mapped_column(String(64), default="saas") # cloud, saas, internal, database, git
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)

class Resource(Base, TenantScopedMixin):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"res_{uuid.uuid4().hex[:12]}")
    application_id: Mapped[str] = mapped_column(String(64), ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    resource_type: Mapped[str] = mapped_column(String(64)) # bucket, db_table, repository, cluster, api_endpoint
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)

class SystemRole(Base, TenantScopedMixin):
    __tablename__ = "system_roles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"srl_{uuid.uuid4().hex[:12]}")
    application_id: Mapped[str] = mapped_column(String(64), ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_privileged: Mapped[bool] = mapped_column(Boolean, default=False)

class Entitlement(Base, TenantScopedMixin):
    __tablename__ = "entitlements"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"ent_{uuid.uuid4().hex[:12]}")
    application_id: Mapped[str] = mapped_column(String(64), ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("resources.id", ondelete="SET NULL"), nullable=True)
    permission_name: Mapped[str] = mapped_column(String(128), index=True)
    permission_type: Mapped[str] = mapped_column(String(32), default="custom") # read, write, create, delete, manage, administer, custom
    risk_level: Mapped[str] = mapped_column(String(32), default="low") # low, medium, high, critical
