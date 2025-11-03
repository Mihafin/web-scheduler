from __future__ import annotations

from datetime import datetime, timezone
from fastapi import Header
from sqlalchemy.orm import Session
from . import models


def get_remote_user(x_remote_user: str | None = Header(default=None)) -> str | None:
    return x_remote_user


def _utc_now_iso() -> str:
    # ISO without microseconds, UTC with 'Z'
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_audit_log(
    db: Session,
    username: str | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
    details: str | None = None,
) -> None:
    log = models.AuditLog(
        ts=_utc_now_iso(),
        username=username,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    db.commit()


