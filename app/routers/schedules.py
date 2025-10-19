from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_, text
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
    selected_tag_values: list[models.TagValue] = []
    if data.tagValueIds:
        selected_tag_values = db.query(models.TagValue).filter(models.TagValue.id.in_(data.tagValueIds)).all()
        if len(selected_tag_values) != len(set(data.tagValueIds)):
            raise HTTPException(status_code=400, detail="Some tagValueIds not found")

    # 1) Проверка: указаны все required теги
    required_tags = db.query(models.Tag).filter(models.Tag.required == True).all()
    if required_tags:
        tag_id_to_selected_value_ids: dict[int, list[int]] = {}
        for tv in selected_tag_values:
            tag_id_to_selected_value_ids.setdefault(tv.tag_id, []).append(tv.id)
        missing_tag_names = [t.name for t in required_tags if t.id not in tag_id_to_selected_value_ids]
        if missing_tag_names:
            raise HTTPException(status_code=400, detail=f"Missing required tags: {', '.join(missing_tag_names)}")

    # 2) Проверка: уникальные ресурсы не пересекаются по времени
    unique_tags = db.query(models.Tag).filter(models.Tag.unique_resource == True).all()
    if unique_tags and selected_tag_values:
        # сгруппировать выбранные значения по тегу
        tag_id_to_values: dict[int, list[models.TagValue]] = {}
        for tv in selected_tag_values:
            tag_id_to_values.setdefault(tv.tag_id, []).append(tv)
        unique_tag_ids = {t.id for t in unique_tags}
        for tag_id in unique_tag_ids:
            t_values = tag_id_to_values.get(tag_id, [])
            if not t_values:
                continue
            # для каждого значения проверяем пересечения с уже существующими расписаниями
            value_ids = [tv.id for tv in t_values]
            # найти существующие события, у которых есть одно из value_ids и которые пересекаются по времени
            existing = (
                db.query(models.Schedule)
                .join(models.Schedule.tag_values)
                .filter(
                    models.TagValue.id.in_(value_ids),
                    ~(models.Schedule.date_to < data.dateFrom),
                    ~(models.Schedule.date_from > data.dateTo),
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Time intersects with schedule id={existing.id} for unique resource tag",
                )

    sched.tag_values = selected_tag_values
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


