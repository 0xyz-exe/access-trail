"""Audit evidence export package generator."""
import csv
import io
import json
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.security import sanitize_csv_cell
from backend.app.models.audit_event import AuditEvent
from backend.app.models.access_review import ReviewCampaign, ReviewDecision
from backend.app.models.revocation import RevocationRequest
from backend.app.models.risk_finding import RiskFinding
from backend.app.services.audit_service import AuditService

class ExportService:
    @staticmethod
    def generate_evidence_package(db: Session, tenant_id: str, actor_id: str, actor_name: str) -> dict:
        """Create a complete audit evidence package containing campaigns, decisions, revocations, and audit chain verification."""
        # 1. Audit integrity status
        integrity_check = AuditService.verify_chain(db, tenant_id)

        # 2. Campaigns & decisions
        campaigns = list(db.execute(select(ReviewCampaign).where(ReviewCampaign.tenant_id == tenant_id)).scalars().all())
        decisions = list(db.execute(select(ReviewDecision).where(ReviewDecision.tenant_id == tenant_id)).scalars().all())
        revocations = list(db.execute(select(RevocationRequest).where(RevocationRequest.tenant_id == tenant_id)).scalars().all())
        findings = list(db.execute(select(RiskFinding).where(RiskFinding.tenant_id == tenant_id)).scalars().all())

        now = datetime.now(timezone.utc)
        package = {
            "metadata": {
                "generated_at": now.isoformat(),
                "tenant_id": tenant_id,
                "exported_by": actor_name,
                "framework_reference": "Zero Trust IAM & Least Privilege Audit Evidence Package",
            },
            "integrity_verification": integrity_check,
            "campaigns": [
                {
                    "id": c.id,
                    "name": c.name,
                    "scope": c.scope,
                    "status": c.status,
                    "total_items": c.total_items,
                    "reviewed_items": c.reviewed_items,
                    "due_date": c.due_date.isoformat(),
                }
                for c in campaigns
            ],
            "decisions": [
                {
                    "id": d.id,
                    "campaign_id": d.campaign_id,
                    "identity_id": d.identity_id,
                    "grant_id": d.grant_id,
                    "decision": d.decision,
                    "comments": d.comments,
                    "decided_at": d.decided_at.isoformat(),
                }
                for d in decisions
            ],
            "revocations": [
                {
                    "id": r.id,
                    "grant_id": r.grant_id,
                    "identity_id": r.identity_id,
                    "status": r.status,
                    "target_system": r.target_system,
                    "executed_at": r.executed_at.isoformat() if r.executed_at else None,
                }
                for r in revocations
            ],
            "findings_summary": {
                "total": len(findings),
                "critical": sum(1 for f in findings if f.severity == "critical"),
                "high": sum(1 for f in findings if f.severity == "high"),
                "medium": sum(1 for f in findings if f.severity == "medium"),
                "low": sum(1 for f in findings if f.severity == "low"),
            }
        }

        AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_name=actor_name,
            action="report.export_evidence_package",
            target_entity="evidence_package",
            category="administration",
            metadata={"total_campaigns": len(campaigns), "total_decisions": len(decisions)}
        )

        return package
