"""Identity management service with CSV import/export."""
import csv
import io
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from backend.app.core.security import sanitize_csv_cell
from backend.app.models.identity import Identity
from backend.app.services.audit_service import AuditService

class IdentityService:
    @staticmethod
    def list_identities(
        db: Session,
        tenant_id: str,
        search: str | None = None,
        identity_type: str | None = None,
        status: str | None = None,
        department: str | None = None,
        is_privileged: bool | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Identity]:
        stmt = select(Identity).where(Identity.tenant_id == tenant_id)
        if search:
            search_filter = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Identity.username.ilike(search_filter),
                    Identity.full_name.ilike(search_filter),
                    Identity.email.ilike(search_filter)
                )
            )
        if identity_type:
            stmt = stmt.where(Identity.identity_type == identity_type)
        if status:
            stmt = stmt.where(Identity.status == status)
        if department:
            stmt = stmt.where(Identity.department == department)
        if is_privileged is not None:
            stmt = stmt.where(Identity.is_privileged == is_privileged)

        stmt = stmt.order_by(Identity.created_at.desc()).offset(offset).limit(limit)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def export_csv(db: Session, tenant_id: str) -> str:
        """Export all identities to CSV safely mitigating formula injection."""
        stmt = select(Identity).where(Identity.tenant_id == tenant_id).order_by(Identity.username.asc())
        identities = list(db.execute(stmt).scalars().all())

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Username", "Email", "FullName", "Type", "Status",
            "Department", "ManagerEmail", "IsPrivileged", "RiskScore", "Source"
        ])
        for idn in identities:
            writer.writerow([
                sanitize_csv_cell(idn.id),
                sanitize_csv_cell(idn.username),
                sanitize_csv_cell(idn.email or ""),
                sanitize_csv_cell(idn.full_name),
                sanitize_csv_cell(idn.identity_type),
                sanitize_csv_cell(idn.status),
                sanitize_csv_cell(idn.department or ""),
                sanitize_csv_cell(idn.manager_email or ""),
                idn.is_privileged,
                idn.risk_score,
                sanitize_csv_cell(idn.source_system),
            ])
        return output.getvalue()

    @staticmethod
    def import_csv(db: Session, tenant_id: str, csv_content: str, actor_id: str, actor_name: str) -> dict:
        """Import identities from CSV content."""
        f = io.StringIO(csv_content.strip())
        reader = csv.DictReader(f)
        created_count = 0
        errors = []

        for row_idx, row in enumerate(reader, start=2):
            username = row.get("Username", "").strip()
            full_name = row.get("FullName", "").strip()
            if not username or not full_name:
                errors.append(f"Row {row_idx}: Missing required Username or FullName.")
                continue

            existing = db.execute(
                select(Identity).where(Identity.tenant_id == tenant_id, Identity.username == username)
            ).scalars().first()
            if existing:
                errors.append(f"Row {row_idx}: Identity '{username}' already exists.")
                continue

            is_priv = row.get("IsPrivileged", "false").lower() in ("true", "1", "yes")
            risk_score = int(row.get("RiskScore", 0)) if row.get("RiskScore", "").isdigit() else 0

            new_idn = Identity(
                tenant_id=tenant_id,
                username=username,
                email=row.get("Email") or None,
                full_name=full_name,
                identity_type=row.get("Type", "human"),
                status=row.get("Status", "active"),
                department=row.get("Department") or None,
                manager_email=row.get("ManagerEmail") or None,
                is_privileged=is_priv,
                risk_score=risk_score,
                source_system=row.get("Source", "csv_import"),
            )
            db.add(new_idn)
            created_count += 1

        db.commit()

        AuditService.log_event(
            db=db,
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_name=actor_name,
            action="identity.import_csv",
            target_entity=f"identities_count_{created_count}",
            category="administration",
            metadata={"created_count": created_count, "error_count": len(errors)}
        )

        return {"created_count": created_count, "errors": errors}
