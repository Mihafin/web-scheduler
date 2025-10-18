from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas


router = APIRouter(prefix="/tags", tags=["tag_values"])


@router.get("/{tag_id}/values", response_model=list[schemas.TagValueOut])
def list_tag_values(tag_id: int, db: Session = Depends(get_db)):
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return db.query(models.TagValue).filter(models.TagValue.tag_id == tag_id).order_by(models.TagValue.value).all()


@router.post("/{tag_id}/values", response_model=schemas.TagValueOut)
def create_tag_value(tag_id: int, data: schemas.TagValueCreate, db: Session = Depends(get_db)):
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    dup = (
        db.query(models.TagValue)
        .filter(models.TagValue.tag_id == tag_id, models.TagValue.value == data.value)
        .first()
    )
    if dup:
        raise HTTPException(status_code=400, detail="Value already exists for this tag")
    tv = models.TagValue(tag_id=tag_id, value=data.value)
    db.add(tv)
    db.commit()
    db.refresh(tv)
    return tv


@router.put("/values/{id}", response_model=schemas.TagValueOut)
def update_tag_value(id: int, data: schemas.TagValueUpdate, db: Session = Depends(get_db)):
    tv = db.get(models.TagValue, id)
    if not tv:
        raise HTTPException(status_code=404, detail="Tag value not found")
    if data.value:
        dup = (
            db.query(models.TagValue)
            .filter(models.TagValue.tag_id == tv.tag_id, models.TagValue.value == data.value, models.TagValue.id != id)
            .first()
        )
        if dup:
            raise HTTPException(status_code=400, detail="Value already exists for this tag")
        tv.value = data.value
    db.commit()
    db.refresh(tv)
    return tv


@router.delete("/values/{id}", status_code=204)
def delete_tag_value(id: int, db: Session = Depends(get_db)):
    tv = db.get(models.TagValue, id)
    if not tv:
        raise HTTPException(status_code=404, detail="Tag value not found")
    db.delete(tv)
    db.commit()
    return None


