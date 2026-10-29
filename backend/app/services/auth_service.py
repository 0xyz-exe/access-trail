"""Authentication and RBAC service."""
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.security import hash_password, verify_password, generate_session_token
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.models.organization import Organization

# Role hierarchy and allowed permissions
ROLE_PERMISSIONS = {
    "platform_owner": {"*"},
    "security_admin": {
        "identities:read", "identities:write", "permissions:read", "permissions:write",
        "reviews:read", "reviews:write", "revocations:read", "revocations:write",
        "findings:read", "findings:write", "policies:read", "policies:write",
        "connectors:read", "connectors:write", "audit:read", "reports:read"
    },
    "access_reviewer": {
        "identities:read", "permissions:read", "reviews:read", "reviews:write",
        "revocations:read", "findings:read"
    },
    "auditor": {
        "identities:read", "permissions:read", "reviews:read", "revocations:read",
        "findings:read", "policies:read", "audit:read", "audit:verify", "reports:read"
    },
    "read_only_analyst": {
        "identities:read", "permissions:read", "reviews:read", "revocations:read",
        "findings:read", "dashboard:read"
    },
    "standard_user": {
        "profile:read"
    }
}

class AuthService:
    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User | None:
        stmt = select(User).where(User.email == email, User.is_active == True)
        user = db.execute(stmt).scalars().first()
        if not user or not verify_password(password, user.password_hash):
            return None
        # Update or set active session token
        user.session_token = generate_session_token()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_token(db: Session, token: str) -> User | None:
        if not token:
            return None
        stmt = select(User).where(User.session_token == token, User.is_active == True)
        return db.execute(stmt).scalars().first()

    @staticmethod
    def check_permission(user: User, required_permission: str) -> bool:
        user_perms = ROLE_PERMISSIONS.get(user.role, set())
        return "*" in user_perms or required_permission in user_perms

def get_current_user(
    authorization: str | None = Header(None),
    x_session_token: str | None = Header(None),
    db: Session = Depends(get_db)
) -> User:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif x_session_token:
        token = x_session_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials."
        )

    user = AuthService.get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token."
        )
    return user

def require_role(*allowed_roles: str):
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles and user.role != "platform_owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}. Current role: {user.role}"
            )
        return user
    return role_checker
