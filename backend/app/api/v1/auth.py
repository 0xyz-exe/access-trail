"""Auth router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserOut
from backend.app.services.auth_service import AuthService, get_current_user
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService.authenticate(db, req.email, req.password)
    if not user:
        AuditService.log_event(
            db=db,
            tenant_id="default_tenant",
            actor_id="anonymous",
            actor_name=req.email,
            action="auth.login_failed",
            target_entity="auth_endpoint",
            category="security",
            result="denied",
            metadata={"email": req.email}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials."
        )

    AuditService.log_event(
        db=db,
        tenant_id=user.tenant_id,
        actor_id=user.id,
        actor_name=user.full_name,
        action="auth.login_success",
        target_entity="user_session",
        category="security",
        result="success",
        metadata={"role": user.role}
    )

    return TokenResponse(
        access_token=user.session_token or "",
        token_type="bearer",
        user=UserOut.model_validate(user)
    )

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.session_token = None
    db.commit()
    return {"message": "Logged out successfully."}
