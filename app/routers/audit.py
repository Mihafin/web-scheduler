from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[schemas.AuditEntryOut])
def list_audit(days: int = Query(2, ge=1, le=365), db: Session = Depends(get_db)):
    threshold = (datetime.now(timezone.utc) - timedelta(days=days)).replace(microsecond=0)
    # Store and compare as ISO strings in UTC
    threshold_iso = threshold.isoformat().replace("+00:00", "Z")
    rows = (
        db.query(models.AuditLog)
        .filter(models.AuditLog.ts >= threshold_iso)
        .order_by(models.AuditLog.ts.desc(), models.AuditLog.id.desc())
        .all()
    )
    result: list[schemas.AuditEntryOut] = []
    for r in rows:
        result.append(
            schemas.AuditEntryOut(
                id=r.id,
                ts=r.ts,
                username=r.username,
                action=r.action,
                entity=r.entity,
                entityId=r.entity_id,
                details=r.details,
            )
        )
    return result


