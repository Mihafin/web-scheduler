from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas


router = APIRouter(prefix="/schedules", tags=["schedules"])


def _intersects(a_from: str, a_to: str, b_from: str, b_to: str) -> bool:
    return not (a_to < b_from or a_from > b_to)


@router.get("", response_model=list[schemas.ScheduleOut])
def list_schedules(
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
    tag_value_ids: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Schedule)
    if from_ and to:
        # Храним как строки ISO; фильтруем по пересечению диапазонов
        q = q.filter(~(models.Schedule.date_to < from_), ~(models.Schedule.date_from > to))
    if tag_value_ids:
        ids = [int(x) for x in tag_value_ids.split(",") if x]
        if ids:
            # Группируем выбранные значения по тегу и требуем наличие хотя бы одного
            # значения из каждой группы (И между группами, ИЛИ внутри группы)
            selected_values = (
                db.query(models.TagValue)
                .filter(models.TagValue.id.in_(ids))
                .all()
            )
            tag_id_to_value_ids: dict[int, list[int]] = {}
            for tv in selected_values:
                tag_id_to_value_ids.setdefault(tv.tag_id, []).append(tv.id)
            for value_ids in tag_id_to_value_ids.values():
                q = q.filter(models.Schedule.tag_values.any(models.TagValue.id.in_(value_ids)))
    rows = q.all()
    result: list[schemas.ScheduleOut] = []
    for s in rows:
        result.append(
            schemas.ScheduleOut(
                id=s.id,
                title=s.title,
                dateFrom=s.date_from,
                dateTo=s.date_to,
                tagValueIds=[tv.id for tv in s.tag_values],
            )
        )
    return result


@router.post("", response_model=schemas.ScheduleOut)
def create_schedule(data: schemas.ScheduleCreate, db: Session = Depends(get_db)):
    if data.dateTo < data.dateFrom:
        raise HTTPException(status_code=400, detail="dateTo must be >= dateFrom")
    sched = models.Schedule(title=data.title, date_from=data.dateFrom, date_to=data.dateTo)
    if data.tagValueIds:
        tag_values = db.query(models.TagValue).filter(models.TagValue.id.in_(data.tagValueIds)).all()
        if len(tag_values) != len(set(data.tagValueIds)):
            raise HTTPException(status_code=400, detail="Some tagValueIds not found")
        sched.tag_values = tag_values
    db.add(sched)
    db.commit()
    db.refresh(sched)
    return schemas.ScheduleOut(
        id=sched.id,
        title=sched.title,
        dateFrom=sched.date_from,
        dateTo=sched.date_to,
        tagValueIds=[tv.id for tv in sched.tag_values],
    )


@router.put("/{id}", response_model=schemas.ScheduleOut)
def update_schedule(id: int, data: schemas.ScheduleUpdate, db: Session = Depends(get_db)):
    sched = db.get(models.Schedule, id)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    if data.title is not None:
        sched.title = data.title
    if data.dateFrom is not None:
        sched.date_from = data.dateFrom
    if data.dateTo is not None:
        sched.date_to = data.dateTo
    if data.dateFrom is not None and data.dateTo is not None and data.dateTo < data.dateFrom:
        raise HTTPException(status_code=400, detail="dateTo must be >= dateFrom")
    if data.tagValueIds is not None:
        tag_values = db.query(models.TagValue).filter(models.TagValue.id.in_(data.tagValueIds)).all()
        if len(tag_values) != len(set(data.tagValueIds)):
            raise HTTPException(status_code=400, detail="Some tagValueIds not found")
        sched.tag_values = tag_values
    db.commit()
    db.refresh(sched)
    return schemas.ScheduleOut(
        id=sched.id,
        title=sched.title,
        dateFrom=sched.date_from,
        dateTo=sched.date_to,
        tagValueIds=[tv.id for tv in sched.tag_values],
    )


@router.delete("/{id}", status_code=204)
def delete_schedule(id: int, db: Session = Depends(get_db)):
    sched = db.get(models.Schedule, id)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(sched)
    db.commit()
    return None


