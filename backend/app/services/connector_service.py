"""Connector synchronization and external Mock IdP integration."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.connector import ConnectorConfig
from backend.app.models.identity import Identity
from backend.app.models.permission import Application, Entitlement
from backend.app.models.access_grant import AccessGrant
from backend.app.models.user import User
from backend.app.services.audit_service import AuditService

class ConnectorService:
    @staticmethod
    def sync_mock_idp(db: Session, tenant_id: str, connector_id: str, actor: User) -> dict:
        """Simulate syncing external identities & grants from enterprise IdP."""
        connector = db.execute(
            select(ConnectorConfig).where(ConnectorConfig.id == connector_id, ConnectorConfig.tenant_id == tenant_id)
        ).scalars().first()
        if not connector:
            return {"error": "Connector not found"}

        now = datetime.now(timezone.utc)
        synced_identities = 0

        # Sync mock identities
        mock_data = [
            ("devops.svc", "devops-service@internal.net", "DevOps Pipeline Runner", "service_account", "Platform Eng", "platform-lead@corp.net", True),
            ("sarah.connor", "sarah.connor@corp.net", "Sarah Connor", "human", "Security", "ciso@corp.net", True),
            ("guest.contractor", "contractor.guest@ext-vendor.com", "Guest Contractor", "contractor", "QA", "qa-lead@corp.net", False),
        ]

        for username, email, full_name, idn_type, dept, mgr, is_priv in mock_data:
            existing = db.execute(
                select(Identity).where(Identity.tenant_id == tenant_id, Identity.username == username)
            ).scalars().first()
            if not existing:
                new_idn = Identity(
                    tenant_id=tenant_id,
                    username=username,
                    email=email,
                    full_name=full_name,
                    identity_type=idn_type,
                    status="active",
                    department=dept,
                    manager_email=mgr,
                    is_privileged=is_priv,
                    source_system="mock_idp",
                    last_sync_at=now,
                    last_active_at=now
                )
                db.add(new_idn)
                synced_identities += 1
            else:
                existing.last_sync_at = now

        connector.last_sync_at = now
        connector.sync_count += 1
        connector.status = "healthy"
        db.commit()

        AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            actor_id=actor.id,
            actor_name=actor.full_name,
            action="connector.sync",
            target_entity=connector.id,
            category="administration",
            metadata={"synced_identities": synced_identities, "connector_type": connector.connector_type}
        )

        return {"synced_identities": synced_identities, "status": "completed"}
