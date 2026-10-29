"""Connectors and mock synchronization router."""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.connector import ConnectorConfig
from backend.app.models.user import User
from backend.app.services.auth_service import get_current_user, require_role
from backend.app.services.connector_service import ConnectorService

router = APIRouter(prefix="/connectors", tags=["connectors"])

class ConnectorOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    connector_type: str
    status: str
    sync_count: int
    last_sync_at: str | None = None

    model_config = {"from_attributes": True}

@router.get("", response_model=list[ConnectorOut])
def get_connectors(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(ConnectorConfig).where(ConnectorConfig.tenant_id == current_user.tenant_id)
    connectors = list(db.execute(stmt).scalars().all())
    return [
        ConnectorOut(
            id=c.id,
            tenant_id=c.tenant_id,
            name=c.name,
            connector_type=c.connector_type,
            status=c.status,
            sync_count=c.sync_count,
            last_sync_at=c.last_sync_at.isoformat() if c.last_sync_at else None
        )
        for c in connectors
    ]

@router.post("/{connector_id}/sync")
def sync_connector(
    connector_id: str,
    current_user: User = Depends(require_role("platform_owner", "security_admin")),
    db: Session = Depends(get_db)
):
    result = ConnectorService.sync_mock_idp(db, current_user.tenant_id, connector_id, current_user)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
