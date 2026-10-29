"""Tamper-evident audit event service with hash-chaining verification."""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.security import canonical_json, calculate_event_hash
from backend.app.models.audit_event import AuditEvent

class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        tenant_id: str,
        actor_id: str,
        actor_name: str,
        action: str,
        target_entity: str,
        category: str = "security",
        result: str = "success",
        metadata: dict | None = None
    ) -> AuditEvent:
        """Create and append an audit event with SHA-256 hash chaining."""
        metadata = metadata or {}

        # Fetch last event for tenant to get previous hash
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id)
            .order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc())
            .limit(1)
        )
        last_event = db.execute(stmt).scalars().first()
        prev_hash = last_event.event_hash if last_event else "0" * 64

        now = datetime.now(timezone.utc)
        payload = {
            "tenant_id": tenant_id,
            "timestamp": now.isoformat(),
            "actor_id": actor_id,
            "actor_name": actor_name,
            "action": action,
            "target_entity": target_entity,
            "category": category,
            "result": result,
            "metadata": metadata,
        }
        canonical_str = canonical_json(payload)
        event_hash = calculate_event_hash(prev_hash, canonical_str)

        audit_entry = AuditEvent(
            tenant_id=tenant_id,
            timestamp=now,
            actor_id=actor_id,
            actor_name=actor_name,
            action=action,
            target_entity=target_entity,
            category=category,
            result=result,
            metadata_json=canonical_str,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def verify_chain(db: Session, tenant_id: str) -> dict:
        """Verify the integrity of the tenant's hash chain."""
        stmt = (
            select(AuditEvent)
            .where(AuditEvent.tenant_id == tenant_id)
            .order_by(AuditEvent.timestamp.asc(), AuditEvent.id.asc())
        )
        events = list(db.execute(stmt).scalars().all())

        if not events:
            return {
                "total_events": 0,
                "is_valid": True,
                "broken_event_id": None,
                "details": "Audit chain is empty. No events to verify."
            }

        expected_prev_hash = "0" * 64
        for event in events:
            if event.prev_hash != expected_prev_hash:
                return {
                    "total_events": len(events),
                    "is_valid": False,
                    "broken_event_id": event.id,
                    "details": f"Chain broken at event {event.id}: prev_hash mismatch. Expected {expected_prev_hash}, got {event.prev_hash}."
                }

            # Recompute event hash from canonical metadata
            computed_hash = calculate_event_hash(event.prev_hash, event.metadata_json)
            if computed_hash != event.event_hash:
                return {
                    "total_events": len(events),
                    "is_valid": False,
                    "broken_event_id": event.id,
                    "details": f"Tampering detected at event {event.id}: payload hash mismatch."
                }
            expected_prev_hash = event.event_hash

        return {
            "total_events": len(events),
            "is_valid": True,
            "broken_event_id": None,
            "details": f"All {len(events)} events cryptographically verified."
        }
