"""Revocations router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.review import RevocationRequestOut
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.revocation_service import RevocationService

router = APIRouter(prefix="/revocations", tags=["revocations"])

@router.get("", response_model=list[RevocationRequestOut])
def get_revocation_requests(
    status: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return RevocationService.list_requests(db, current_user.tenant_id, status)

@router.post("/{request_id}/approve", response_model=RevocationRequestOut)
def approve_revocation(
    request_id: str,
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    return RevocationService.approve_request(db, current_user.tenant_id, request_id, current_user)

@router.post("/{request_id}/execute", response_model=RevocationRequestOut)
def execute_revocation(
    request_id: str,
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    return RevocationService.execute_revocation(db, current_user.tenant_id, request_id, current_user)
