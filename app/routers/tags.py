from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, engine, Base
from sqlalchemy import text
from .. import models, schemas
from ..utils import get_remote_user, write_audit_log


router = APIRouter(prefix="/tags", tags=["tags"])


@router.on_event("startup")
def _create_tables():
    Base.metadata.create_all(bind=engine)
    # Мягкая миграция: добавить столбец color, если его нет
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE tag_values ADD COLUMN color TEXT NULL"))
    except Exception:
        pass
    # Мягкая миграция: добавить столбцы required и unique_resource к tags, если их нет
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE tags ADD COLUMN required BOOLEAN NOT NULL DEFAULT 0"))
    except Exception:
        pass
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE tags ADD COLUMN unique_resource BOOLEAN NOT NULL DEFAULT 0"))
    except Exception:
        pass
    # Мягкая миграция: добавить признак отмены для расписаний
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE schedules ADD COLUMN is_canceled BOOLEAN NOT NULL DEFAULT 0"))
    except Exception:
        pass


@router.get("", response_model=list[schemas.TagOut])
def list_tags(db: Session = Depends(get_db)):
    return db.query(models.Tag).order_by(models.Tag.name).all()


@router.post("", response_model=schemas.TagOut)
def create_tag(data: schemas.TagCreate, db: Session = Depends(get_db), user: str | None = Depends(get_remote_user)):
    exists = db.query(models.Tag).filter(models.Tag.name == data.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Tag with this name already exists")
    tag = models.Tag(name=data.name, required=data.required, unique_resource=data.unique_resource)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    try:
        write_audit_log(db, user, "CREATE", "tags", tag.id, details=f"name={tag.name}; required={tag.required}; unique_resource={tag.unique_resource}")
    except Exception:
        pass
    return tag


@router.put("/{tag_id}", response_model=schemas.TagOut)
def update_tag(tag_id: int, data: schemas.TagUpdate, db: Session = Depends(get_db), user: str | None = Depends(get_remote_user)):
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if data.name:
        dup = db.query(models.Tag).filter(models.Tag.name == data.name, models.Tag.id != tag_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="Tag with this name already exists")
        tag.name = data.name
    # Обновление флагов, если переданы
    if hasattr(data, "required") and data.required is not None:
        tag.required = data.required
    if hasattr(data, "unique_resource") and data.unique_resource is not None:
        tag.unique_resource = data.unique_resource
    db.commit()
    db.refresh(tag)
    try:
        write_audit_log(db, user, "UPDATE", "tags", tag.id, details=f"name={tag.name}; required={tag.required}; unique_resource={tag.unique_resource}")
    except Exception:
        pass
    return tag


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db), user: str | None = Depends(get_remote_user)):
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
    try:
        write_audit_log(db, user, "DELETE", "tags", tag_id)
    except Exception:
        pass
    return None


