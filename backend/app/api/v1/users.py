"""Users management router."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import UserOut
from backend.app.services.auth_service import get_current_user, require_role

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=list[UserOut])
def list_users(
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    stmt = select(User).where(User.tenant_id == current_user.tenant_id).order_by(User.full_name.asc())
    return list(db.execute(stmt).scalars().all())
