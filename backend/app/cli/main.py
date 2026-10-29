"""CLI tool for database seeding, audit verification, and risk scans."""
import argparse
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from backend.app.core.security import hash_password
from backend.app.db.session import SessionLocal, init_db
from backend.app.models.organization import Organization
from backend.app.models.user import User
from backend.app.models.identity import Identity
from backend.app.models.permission import Application, Resource, SystemRole, Entitlement
from backend.app.models.access_grant import AccessGrant
from backend.app.models.access_review import ReviewCampaign, ReviewDecision
from backend.app.models.revocation import RevocationRequest
from backend.app.models.policy import AccessPolicy
from backend.app.models.connector import ConnectorConfig
from backend.app.services.audit_service import AuditService
from backend.app.services.risk_engine import RiskEngine

def seed_demo():
    print("🌱 Initializing database schema...")
    init_db()
    db = SessionLocal()

    try:
        # 1. Organization
        tenant_id = "org_acme_corp"
        org = db.execute(select(Organization).where(Organization.id == tenant_id)).scalars().first()
        if not org:
            org = Organization(
                id=tenant_id,
                name="Acme Financial Corp",
                slug="acme-corp",
                description="Global Financial Services & Fintech Operations"
            )
            db.add(org)
            db.commit()
            print("  Created organization: Acme Financial Corp")

        # 2. Users (Roles)
        users_data = [
            ("admin@acme.corp", "Alice Vance (Platform Admin)", "platform_owner", "Password123!"),
            ("secadmin@acme.corp", "Marcus Ray (Security Admin)", "security_admin", "Password123!"),
            ("reviewer@acme.corp", "Elena Rostova (Access Reviewer)", "access_reviewer", "Password123!"),
            ("auditor@acme.corp", "David Thorne (External Auditor)", "auditor", "Password123!"),
            ("analyst@acme.corp", "Sophie Lin (SOC Analyst)", "read_only_analyst", "Password123!"),
        ]

        created_users = {}
        for email, full_name, role, password in users_data:
            user = db.execute(select(User).where(User.email == email)).scalars().first()
            if not user:
                user = User(
                    tenant_id=tenant_id,
                    email=email,
                    full_name=full_name,
                    role=role,
                    password_hash=hash_password(password),
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            created_users[role] = user
        print(f"  Created {len(users_data)} role-based test users (Password: Password123!)")

        # 3. Applications
        apps_data = [
            ("app_aws", "AWS Cloud Infrastructure", "Production Cloud VPC & Workloads", "cloud", True),
            ("app_k8s", "Production Kubernetes Cluster", "EKS Core Platform Cluster", "cloud", True),
            ("app_github", "GitHub Enterprise", "Source Repositories & CI/CD Actions", "git", False),
            ("app_pg", "PostgreSQL Primary Database", "Core Transactional Ledger DB", "database", True),
            ("app_salesforce", "Salesforce CRM", "Customer & Billing Management", "saas", False),
        ]
        created_apps = {}
        for app_id, name, desc, app_type, is_sens in apps_data:
            app = db.execute(select(Application).where(Application.id == app_id)).scalars().first()
            if not app:
                app = Application(
                    id=app_id,
                    tenant_id=tenant_id,
                    name=name,
                    description=desc,
                    app_type=app_type,
                    is_sensitive=is_sens
                )
                db.add(app)
                db.commit()
                db.refresh(app)
            created_apps[app_id] = app

        # 4. Entitlements
        ents_data = [
            ("ent_aws_iam", "app_aws", "IAM:FullAccess", "administer", "critical"),
            ("ent_aws_s3", "app_aws", "S3:ReadAllBuckets", "read", "medium"),
            ("ent_aws_ec2", "app_aws", "EC2:TerminateInstances", "manage", "high"),
            ("ent_k8s_admin", "app_k8s", "cluster-admin", "administer", "critical"),
            ("ent_k8s_dev", "app_k8s", "developer-readonly", "read", "low"),
            ("ent_gh_admin", "app_github", "repo:admin", "manage", "high"),
            ("ent_gh_write", "app_github", "repo:write", "write", "medium"),
            ("ent_pg_super", "app_pg", "db:superuser", "administer", "critical"),
            ("ent_pg_ro", "app_pg", "db:readonly", "read", "low"),
        ]
        created_ents = {}
        for ent_id, app_id, perm_name, p_type, r_level in ents_data:
            ent = db.execute(select(Entitlement).where(Entitlement.id == ent_id)).scalars().first()
            if not ent:
                ent = Entitlement(
                    id=ent_id,
                    tenant_id=tenant_id,
                    application_id=app_id,
                    permission_name=perm_name,
                    permission_type=p_type,
                    risk_level=r_level
                )
                db.add(ent)
                db.commit()
                db.refresh(ent)
            created_ents[ent_id] = ent

        # 5. Identities
        now = datetime.now(timezone.utc)
        identities_data = [
            ("idn_alice", "alice.chen", "alice.chen@acme.corp", "Alice Chen", "human", "active", "Architecture", "ciso@acme.corp", True),
            ("idn_bob", "bob.smith", "bob.smith@acme.corp", "Bob Smith", "human", "active", "Engineering", "lead-eng@acme.corp", False),
            ("idn_carol", "carol.danvers", "carol.danvers@acme.corp", "Carol Danvers", "human", "active", "Platform DevSecOps", "lead-eng@acme.corp", True),
            ("idn_root", "root.admin", "root-emergency@acme.corp", "Break-Glass Root Admin", "admin", "active", "Infrastructure", None, True), # Unmanaged!
            ("idn_dave", "dave.miller", "dave.miller@former-contractor.com", "Dave Miller", "contractor", "inactive", "Consulting", "ciso@acme.corp", True), # Inactive retaining perms!
            ("idn_ci", "cicd.pipeline", None, "GitHub Actions CI Runner", "service_account", "active", "DevOps", "lead-eng@acme.corp", True),
            ("idn_backup", "backup.daemon", None, "Legacy Database Backup Bot", "service_account", "active", "IT Operations", None, False), # Unassigned owner!
        ]
        created_idns = {}
        for idn_id, username, email, full_name, idn_type, status, dept, mgr, is_priv in identities_data:
            idn = db.execute(select(Identity).where(Identity.id == idn_id)).scalars().first()
            if not idn:
                idn = Identity(
                    id=idn_id,
                    tenant_id=tenant_id,
                    username=username,
                    email=email,
                    full_name=full_name,
                    identity_type=idn_type,
                    status=status,
                    department=dept,
                    manager_email=mgr,
                    is_privileged=is_priv,
                    last_active_at=now - timedelta(days=2),
                    last_sync_at=now
                )
                db.add(idn)
                db.commit()
                db.refresh(idn)
            created_idns[idn_id] = idn

        # 6. Access Grants
        grants_data = [
            ("gnt_1", "idn_alice", "app_aws", "ent_aws_iam", True, "Promoted to Cloud Architect"),
            ("gnt_2", "idn_alice", "app_github", "ent_gh_admin", True, "Repository administrator"),
            ("gnt_3", "idn_bob", "app_github", "ent_gh_write", True, "Standard dev commits"),
            ("gnt_4", "idn_bob", "app_pg", "ent_pg_ro", True, "Analytics query access"),
            ("gnt_5", "idn_carol", "app_k8s", "ent_k8s_admin", True, "Kubernetes cluster management"),
            ("gnt_6", "idn_carol", "app_aws", "ent_aws_ec2", True, "Fleet restart automation"),
            ("gnt_7", "idn_root", "app_aws", "ent_aws_iam", True, "Emergency break-glass"),
            ("gnt_8", "idn_root", "app_pg", "ent_pg_super", True, "Direct database admin grant"), # Direct admin grant!
            ("gnt_9", "idn_dave", "app_pg", "ent_pg_super", True, "Historical consultant grant"), # Inactive user with grant!
            ("gnt_10", "idn_ci", "app_aws", "ent_aws_ec2", True, "Deployment automation"),
        ]
        created_grants = {}
        for g_id, idn_id, app_id, ent_id, is_direct, just in grants_data:
            gnt = db.execute(select(AccessGrant).where(AccessGrant.id == g_id)).scalars().first()
            if not gnt:
                gnt = AccessGrant(
                    id=g_id,
                    tenant_id=tenant_id,
                    identity_id=idn_id,
                    application_id=app_id,
                    entitlement_id=ent_id,
                    is_direct=is_direct,
                    granted_by="System Provisioner",
                    business_justification=just,
                    status="active"
                )
                db.add(gnt)
                db.commit()
                db.refresh(gnt)
            created_grants[g_id] = gnt

        # 7. Connectors
        conn_data = [
            ("con_okta", "Corporate Okta Workforce IdP", "mock_idp", "healthy", 240),
            ("con_ad", "Active Directory Domain Controller", "mock_entitlements", "healthy", 180),
        ]
        for c_id, name, c_type, status, count in conn_data:
            conn = db.execute(select(ConnectorConfig).where(ConnectorConfig.id == c_id)).scalars().first()
            if not conn:
                conn = ConnectorConfig(
                    id=c_id,
                    tenant_id=tenant_id,
                    name=name,
                    connector_type=c_type,
                    status=status,
                    sync_count=count,
                    last_sync_at=now - timedelta(hours=1)
                )
                db.add(conn)
                db.commit()

        # 8. Access Review Campaign
        camp = db.execute(select(ReviewCampaign).where(ReviewCampaign.id == "cmp_q4_cert")).scalars().first()
        if not camp:
            camp = ReviewCampaign(
                id="cmp_q4_cert",
                tenant_id=tenant_id,
                name="Q4 Privileged Access Certification",
                description="Comprehensive quarterly review of all cloud administrative and database entitlements.",
                scope="privileged_only",
                reviewer_id=created_users["access_reviewer"].id,
                status="active",
                start_date=now - timedelta(days=3),
                due_date=now + timedelta(days=11),
                total_items=6,
                reviewed_items=2
            )
            db.add(camp)
            db.commit()

            # Record sample decisions
            dec1 = ReviewDecision(
                id="dec_01",
                tenant_id=tenant_id,
                campaign_id="cmp_q4_cert",
                reviewer_id=created_users["access_reviewer"].id,
                identity_id="idn_alice",
                grant_id="gnt_1",
                decision="approve",
                comments="Approved. Required for cloud architect responsibilities."
            )
            dec2 = ReviewDecision(
                id="dec_02",
                tenant_id=tenant_id,
                campaign_id="cmp_q4_cert",
                reviewer_id=created_users["access_reviewer"].id,
                identity_id="idn_dave",
                grant_id="gnt_9",
                decision="revoke",
                comments="Revoke immediately: Contractor departed last month."
            )
            db.add_all([dec1, dec2])

            # Spawn revocation request for dec2
            rev_req = RevocationRequest(
                id="rvk_dave_pg",
                tenant_id=tenant_id,
                decision_id="dec_02",
                grant_id="gnt_9",
                identity_id="idn_dave",
                status="requested",
                target_system="app_pg"
            )
            db.add(rev_req)
            db.commit()

        # 9. Policies
        policies_data = [
            ("pol_1", "Mandatory Quarterly Review for Cloud Administrative Roles", "periodic_review"),
            ("pol_2", "Separation of Duties: Prohibit Self-Approval of Privileged Grants", "sod_no_self_approval"),
            ("pol_3", "Dual Approval Required for Production DB Revocations", "admin_justification_required"),
        ]
        for p_id, p_name, r_type in policies_data:
            pol = db.execute(select(AccessPolicy).where(AccessPolicy.id == p_id)).scalars().first()
            if not pol:
                pol = AccessPolicy(
                    id=p_id,
                    tenant_id=tenant_id,
                    name=p_name,
                    rule_type=r_type,
                    is_active=True
                )
                db.add(pol)
                db.commit()

        # 10. Run Risk Engine to populate findings
        findings = RiskEngine.evaluate_risks(db, tenant_id)
        print(f"  Risk Engine evaluated {len(findings)} findings.")

        # 11. Initial Audit Trail with cryptographic hash chaining
        AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            actor_id="system",
            actor_name="System Provisioner",
            action="tenant.provisioned",
            target_entity=tenant_id,
            category="administration",
            metadata={"org": "Acme Financial Corp"}
        )
        AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            actor_id=created_users["platform_owner"].id,
            actor_name=created_users["platform_owner"].full_name,
            action="policy.configured",
            target_entity="pol_1",
            category="security",
            metadata={"policy": "Mandatory Quarterly Review"}
        )
        AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            actor_id=created_users["access_reviewer"].id,
            actor_name=created_users["access_reviewer"].full_name,
            action="review.decision_revoke",
            target_entity="gnt_9",
            category="access_review",
            metadata={"revocation_requested": True, "reason": "Contractor departed"}
        )

        # 12. Verify Audit Chain
        verify_status = AuditService.verify_chain(db, tenant_id)
        print(f"  Audit Chain Integrity: {'✅ VALID' if verify_status['is_valid'] else '❌ BROKEN'}")

        print("✨ Demo data seeded successfully!")
    finally:
        db.close()

def verify_audit():
    init_db()
    db = SessionLocal()
    try:
        tenant_id = "org_acme_corp"
        print(f"Verifying cryptographic audit chain for tenant: {tenant_id}...")
        res = AuditService.verify_chain(db, tenant_id)
        print(f"Result: {res}")
        if not res["is_valid"]:
            sys.exit(1)
    finally:
        db.close()

def scan_risks():
    init_db()
    db = SessionLocal()
    try:
        tenant_id = "org_acme_corp"
        print(f"Executing deterministic risk scan for tenant: {tenant_id}...")
        findings = RiskEngine.evaluate_risks(db, tenant_id)
        for f in findings:
            print(f"[{f.severity.upper()}] {f.rule_name} (Identity: {f.identity_id}) - {f.evidence}")
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="AccessTrail CLI Operations")
    parser.add_argument("command", choices=["seed-demo", "verify-audit", "scan-risks"], help="Command to run")
    args = parser.parse_args()

    if args.command == "seed-demo":
        seed_demo()
    elif args.command == "verify-audit":
        verify_audit()
    elif args.command == "scan-risks":
        scan_risks()

if __name__ == "__main__":
    main()
