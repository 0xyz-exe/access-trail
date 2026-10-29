"""Reports and evidence package router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.export_service import ExportService

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/evidence-package")
def get_evidence_package(
    current_user: User = Depends(require_role("platform_owner", "security_admin", "auditor")),
    db: Session = Depends(get_db)
):
    return ExportService.generate_evidence_package(
        db=db,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        actor_name=current_user.full_name
    )
