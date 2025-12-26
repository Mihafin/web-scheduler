from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db, engine, Base
from .. import models, schemas
from ..utils import get_remote_user, write_audit_log


router = APIRouter(prefix="/subscription-types", tags=["subscription_types"])


@router.on_event("startup")
def _create_subscription_types_table():
    """Создание таблицы subscription_types при запуске."""
    Base.metadata.create_all(bind=engine)


@router.get("", response_model=list[schemas.SubscriptionTypeOut])
def list_subscription_types(db: Session = Depends(get_db)):
    """Получить список всех типов абонементов."""
    types = db.query(models.SubscriptionType).order_by(models.SubscriptionType.name).all()
    return [
        schemas.SubscriptionTypeOut(
            id=t.id,
            name=t.name,
            lessonsCount=t.lessons_count,
            durationDays=t.duration_days
        )
        for t in types
    ]


@router.get("/{type_id}", response_model=schemas.SubscriptionTypeOut)
def get_subscription_type(type_id: int, db: Session = Depends(get_db)):
    """Получить тип абонемента по ID."""
    t = db.get(models.SubscriptionType, type_id)
    if not t:
        raise HTTPException(status_code=404, detail="Subscription type not found")
    return schemas.SubscriptionTypeOut(
        id=t.id,
        name=t.name,
        lessonsCount=t.lessons_count,
        durationDays=t.duration_days
    )


@router.post("", response_model=schemas.SubscriptionTypeOut)
def create_subscription_type(
    data: schemas.SubscriptionTypeCreate,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Создать новый тип абонемента."""
    exists = db.query(models.SubscriptionType).filter(models.SubscriptionType.name == data.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Subscription type with this name already exists")
    
    sub_type = models.SubscriptionType(
        name=data.name,
        lessons_count=data.lessonsCount,
        duration_days=data.durationDays
    )
    db.add(sub_type)
    db.commit()
    db.refresh(sub_type)
    
    try:
        write_audit_log(db, user, "CREATE", "subscription_types", sub_type.id,
                        details=f"name={sub_type.name}; lessons={sub_type.lessons_count}; days={sub_type.duration_days}")
    except Exception:
        pass
    
    return schemas.SubscriptionTypeOut(
        id=sub_type.id,
        name=sub_type.name,
        lessonsCount=sub_type.lessons_count,
        durationDays=sub_type.duration_days
    )


@router.put("/{type_id}", response_model=schemas.SubscriptionTypeOut)
def update_subscription_type(
    type_id: int,
    data: schemas.SubscriptionTypeUpdate,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Обновить тип абонемента."""
    sub_type = db.get(models.SubscriptionType, type_id)
    if not sub_type:
        raise HTTPException(status_code=404, detail="Subscription type not found")
    
    old_name = sub_type.name
    old_lessons = sub_type.lessons_count
    old_days = sub_type.duration_days
    
    if data.name is not None:
        dup = db.query(models.SubscriptionType).filter(
            models.SubscriptionType.name == data.name,
            models.SubscriptionType.id != type_id
        ).first()
        if dup:
            raise HTTPException(status_code=400, detail="Subscription type with this name already exists")
        sub_type.name = data.name
    
    if data.lessonsCount is not None:
        sub_type.lessons_count = data.lessonsCount
    if data.durationDays is not None:
        sub_type.duration_days = data.durationDays
    
    db.commit()
    db.refresh(sub_type)
    
    changes = []
    if sub_type.name != old_name:
        changes.append(f"name: {old_name} -> {sub_type.name}")
    if sub_type.lessons_count != old_lessons:
        changes.append(f"lessons: {old_lessons} -> {sub_type.lessons_count}")
    if sub_type.duration_days != old_days:
        changes.append(f"days: {old_days} -> {sub_type.duration_days}")
    
    try:
        write_audit_log(db, user, "UPDATE", "subscription_types", sub_type.id,
                        details="; ".join(changes) if changes else None)
    except Exception:
        pass
    
    return schemas.SubscriptionTypeOut(
        id=sub_type.id,
        name=sub_type.name,
        lessonsCount=sub_type.lessons_count,
        durationDays=sub_type.duration_days
    )


@router.delete("/{type_id}", status_code=204)
def delete_subscription_type(
    type_id: int,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Удалить тип абонемента."""
    sub_type = db.get(models.SubscriptionType, type_id)
    if not sub_type:
        raise HTTPException(status_code=404, detail="Subscription type not found")
    
    del_details = f"name={sub_type.name}; lessons={sub_type.lessons_count}; days={sub_type.duration_days}"
    db.delete(sub_type)
    db.commit()
    
    try:
        write_audit_log(db, user, "DELETE", "subscription_types", type_id, details=del_details)
    except Exception:
        pass
    
    return None

