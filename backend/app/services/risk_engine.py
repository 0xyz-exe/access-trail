"""Deterministic risk scoring and excessive privilege detection engine."""
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.app.models.identity import Identity
from backend.app.models.access_grant import AccessGrant
from backend.app.models.permission import Entitlement, SystemRole
from backend.app.models.access_review import ReviewCampaign
from backend.app.models.risk_finding import RiskFinding

class RiskEngine:
    @staticmethod
    def evaluate_risks(db: Session, tenant_id: str) -> list[RiskFinding]:
        """Run all deterministic risk rules against current tenant state."""
        # Clean up existing open findings to recalculate freshly
        existing_findings = db.execute(
            select(RiskFinding).where(RiskFinding.tenant_id == tenant_id, RiskFinding.status == "open")
        ).scalars().all()
        for f in existing_findings:
            db.delete(f)
        db.flush()

        now = datetime.now(timezone.utc)
        new_findings: list[RiskFinding] = []

        # Rule 1: Privileged identity without accountable manager
        privileged_unmanaged = db.execute(
            select(Identity).where(
                Identity.tenant_id == tenant_id,
                Identity.is_privileged == True,
                (Identity.manager_email == None) | (Identity.manager_email == "")
            )
        ).scalars().all()
        for idn in privileged_unmanaged:
            new_findings.append(RiskFinding(
                tenant_id=tenant_id,
                identity_id=idn.id,
                finding_type="orphaned_privileged",
                severity="critical",
                rule_name="Unmanaged Privileged Account",
                evidence=f"Identity '{idn.username}' ({idn.identity_type}) has privileged access but no manager/owner recorded.",
                remediation="Assign an active accountable manager or demote administrative privileges."
            ))

        # Rule 2: Inactive identity with active grants
        inactive_with_grants = db.execute(
            select(Identity)
            .join(AccessGrant, AccessGrant.identity_id == Identity.id)
            .where(
                Identity.tenant_id == tenant_id,
                Identity.status == "inactive",
                AccessGrant.status == "active"
            )
            .distinct()
        ).scalars().all()
        for idn in inactive_with_grants:
            new_findings.append(RiskFinding(
                tenant_id=tenant_id,
                identity_id=idn.id,
                finding_type="dormant_privileged",
                severity="high",
                rule_name="Inactive Account Retaining Permissions",
                evidence=f"Identity '{idn.username}' is marked inactive but still retains active permissions.",
                remediation="Initiate immediate access revocation and disable account."
            ))

        # Rule 3: Direct administrative grants
        direct_admin_grants = db.execute(
            select(AccessGrant, Entitlement)
            .join(Entitlement, Entitlement.id == AccessGrant.entitlement_id)
            .where(
                AccessGrant.tenant_id == tenant_id,
                AccessGrant.status == "active",
                AccessGrant.is_direct == True,
                Entitlement.permission_type.in_(["administer", "manage"])
            )
        ).all()
        for grant, ent in direct_admin_grants:
            new_findings.append(RiskFinding(
                tenant_id=tenant_id,
                identity_id=grant.identity_id,
                finding_type="direct_admin_grant",
                severity="high",
                rule_name="Direct Administrative Permission Grant",
                evidence=f"Identity received direct administrative entitlement '{ent.permission_name}' outside role governance.",
                remediation="Replace direct grant with approved role-based entitlement."
            ))

        # Rule 4: Overdue review campaigns
        overdue_campaigns = db.execute(
            select(ReviewCampaign).where(
                ReviewCampaign.tenant_id == tenant_id,
                ReviewCampaign.status == "active",
                ReviewCampaign.due_date < now
            )
        ).scalars().all()
        for cmp in overdue_campaigns:
            cmp.status = "overdue"
            new_findings.append(RiskFinding(
                tenant_id=tenant_id,
                identity_id=None,
                finding_type="overdue_review",
                severity="high",
                rule_name="Access Review Past Due Date",
                evidence=f"Campaign '{cmp.name}' is overdue. Due date was {cmp.due_date.isoformat()}.",
                remediation="Notify assigned reviewers and complete certification decisions."
            ))

        # Rule 5: Expired grants still marked active
        expired_grants = db.execute(
            select(AccessGrant).where(
                AccessGrant.tenant_id == tenant_id,
                AccessGrant.status == "active",
                AccessGrant.expires_at != None,
                AccessGrant.expires_at < now
            )
        ).scalars().all()
        for gnt in expired_grants:
            new_findings.append(RiskFinding(
                tenant_id=tenant_id,
                identity_id=gnt.identity_id,
                finding_type="expired_grant",
                severity="medium",
                rule_name="Expired Access Grant Unrevoked",
                evidence=f"Access grant {gnt.id} expired at {gnt.expires_at} but status is still active.",
                remediation="Execute revocation workflow to prune expired credentials."
            ))

        # Rule 6: Service accounts without owner
        unowned_service_accounts = db.execute(
            select(Identity).where(
                Identity.tenant_id == tenant_id,
                Identity.identity_type.in_(["service_account", "app"]),
                (Identity.manager_email == None) | (Identity.manager_email == "")
            )
        ).scalars().all()
        for sa in unowned_service_accounts:
            new_findings.append(RiskFinding(
                tenant_id=tenant_id,
                identity_id=sa.id,
                finding_type="unassigned_service_account",
                severity="medium",
                rule_name="Service Account Lacks Accountable Owner",
                evidence=f"Service account '{sa.username}' has no accountable engineering owner specified.",
                remediation="Assign responsible team lead or engineering contact."
            ))

        for f in new_findings:
            db.add(f)

        db.commit()

        # Update identity risk scores based on findings count
        for idn in db.execute(select(Identity).where(Identity.tenant_id == tenant_id)).scalars().all():
            crit_count = db.execute(
                select(func.count(RiskFinding.id)).where(
                    RiskFinding.identity_id == idn.id,
                    RiskFinding.severity == "critical",
                    RiskFinding.status == "open"
                )
            ).scalar() or 0
            high_count = db.execute(
                select(func.count(RiskFinding.id)).where(
                    RiskFinding.identity_id == idn.id,
                    RiskFinding.severity == "high",
                    RiskFinding.status == "open"
                )
            ).scalar() or 0
            med_count = db.execute(
                select(func.count(RiskFinding.id)).where(
                    RiskFinding.identity_id == idn.id,
                    RiskFinding.severity == "medium",
                    RiskFinding.status == "open"
                )
            ).scalar() or 0

            calculated_score = min(100, (crit_count * 40) + (high_count * 20) + (med_count * 10))
            idn.risk_score = calculated_score

        db.commit()
        return new_findings
