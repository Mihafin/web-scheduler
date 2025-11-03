from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..utils import get_remote_user, write_audit_log


router = APIRouter(prefix="/tags", tags=["tag_values"])


@router.get("/{tag_id}/values", response_model=list[schemas.TagValueOut])
def list_tag_values(tag_id: int, db: Session = Depends(get_db)):
    tag = db.get(models.Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return db.query(models.TagValue).filter(models.TagValue.tag_id == tag_id).order_by(models.TagValue.value).all()


@router.post("/{tag_id}/values", response_model=schemas.TagValueOut)
def create_tag_value(tag_id: int, data: schemas.TagValueCreate, db: Session = Depends(get_db), user: str | None = Depends(get_remote_user)):
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
    tv = models.TagValue(tag_id=tag_id, value=data.value, color=data.color)
    db.add(tv)
    db.commit()
    db.refresh(tv)
    try:
        write_audit_log(db, user, "CREATE", "tag_values", tv.id, details=f"tag_id={tag_id}; value={tv.value}; color={tv.color}")
    except Exception:
        pass
    return tv


@router.put("/values/{id}", response_model=schemas.TagValueOut)
def update_tag_value(id: int, data: schemas.TagValueUpdate, db: Session = Depends(get_db), user: str | None = Depends(get_remote_user)):
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
    if data.color is not None:
        tv.color = data.color
    db.commit()
    db.refresh(tv)
    try:
        write_audit_log(db, user, "UPDATE", "tag_values", tv.id, details=f"value={tv.value}; color={tv.color}")
    except Exception:
        pass
    return tv


@router.delete("/values/{id}", status_code=204)
def delete_tag_value(id: int, db: Session = Depends(get_db), user: str | None = Depends(get_remote_user)):
    tv = db.get(models.TagValue, id)
    if not tv:
        raise HTTPException(status_code=404, detail="Tag value not found")
    db.delete(tv)
    db.commit()
    try:
        write_audit_log(db, user, "DELETE", "tag_values", id)
    except Exception:
        pass
    return None


