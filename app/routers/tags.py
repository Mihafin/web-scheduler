from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, engine, Base
from sqlalchemy import text
from .. import models, schemas


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


@router.get("", response_model=list[schemas.TagOut])
def list_tags(db: Session = Depends(get_db)):
    return db.query(models.Tag).order_by(models.Tag.name).all()


@router.post("", response_model=schemas.TagOut)
def create_tag(data: schemas.TagCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Tag).filter(models.Tag.name == data.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Tag with this name already exists")
    tag = models.Tag(name=data.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=schemas.TagOut)
def update_tag(tag_id: int, data: schemas.TagUpdate, db: Session = Depends(get_db)):
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if data.name:
        dup = db.query(models.Tag).filter(models.Tag.name == data.name, models.Tag.id != tag_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="Tag with this name already exists")
        tag.name = data.name
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
    return None


