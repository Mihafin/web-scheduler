from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, and_, text
from sqlalchemy.orm import Session
from ..db import get_db
from .. import models, schemas
from ..utils import get_remote_user, write_audit_log


router = APIRouter(prefix="/schedules", tags=["schedules"])


def _intersects(a_from: str, a_to: str, b_from: str, b_to: str) -> bool:
    # Пересечение по полуоткрытым интервалам: [from, to)
    # Не пересекаются, если один заканчивается в момент начала другого
    return not (a_to <= b_from or a_from >= b_to)


@router.get("", response_model=list[schemas.ScheduleOut])
def list_schedules(
    from_: str | None = Query(None, alias="from"),
    to: str | None = None,
    tag_value_ids: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Schedule)
    if from_ and to:
        # Храним как строки ISO; фильтруем по пересечению диапазонов (полуоткрытые интервалы)
        q = q.filter(~(models.Schedule.date_to <= from_), ~(models.Schedule.date_from >= to))
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
                isCanceled=s.is_canceled,
                contact=s.contact,
            )
        )
    return result


@router.post("", response_model=schemas.ScheduleOut)
def create_schedule(data: schemas.ScheduleCreate, db: Session = Depends(get_db), user: str | None = Depends(get_remote_user)):
    if data.dateTo < data.dateFrom:
        raise HTTPException(status_code=400, detail="dateTo must be >= dateFrom")
    sched = models.Schedule(title=data.title, date_from=data.dateFrom, date_to=data.dateTo, contact=data.contact)
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

    # 2) Проверка: уникальные ресурсы не пересекаются по времени (игнорируя отменённые события)
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
                    ~(models.Schedule.date_to <= data.dateFrom),
                    ~(models.Schedule.date_from >= data.dateTo),
                    models.Schedule.is_canceled == False,
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Пересечение с событием \"{existing.title}\" (с {existing.date_from} по {existing.date_to})",
                )

    sched.tag_values = selected_tag_values
    db.add(sched)
    db.commit()
    db.refresh(sched)
    try:
        write_audit_log(db, user, "CREATE", "schedules", sched.id, details=f"title={sched.title}; from={sched.date_from}; to={sched.date_to}")
    except Exception:
        pass
    return schemas.ScheduleOut(
        id=sched.id,
        title=sched.title,
        dateFrom=sched.date_from,
        dateTo=sched.date_to,
        tagValueIds=[tv.id for tv in sched.tag_values],
        isCanceled=sched.is_canceled,
        contact=sched.contact,
    )


@router.put("/{id}", response_model=schemas.ScheduleOut)
def update_schedule(id: int, data: schemas.ScheduleUpdate, db: Session = Depends(get_db), user: str | None = Depends(get_remote_user)):
    sched = db.get(models.Schedule, id)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    # Снимем старые значения для построения diff
    old_title = sched.title
    old_from = sched.date_from
    old_to = sched.date_to
    old_is_canceled = sched.is_canceled
    old_tag_ids = [tv.id for tv in sched.tag_values]
    old_contact = sched.contact
    # Сформируем итоговые значения после обновления (не применяя к БД до валидаций)
    new_title = data.title if data.title is not None else sched.title
    new_from = data.dateFrom if data.dateFrom is not None else sched.date_from
    new_to = data.dateTo if data.dateTo is not None else sched.date_to
    new_is_canceled = data.isCanceled if data.isCanceled is not None else sched.is_canceled
    new_contact = data.contact if data.contact is not None else sched.contact
    if new_to < new_from:
        raise HTTPException(status_code=400, detail="dateTo must be >= dateFrom")
    if data.tagValueIds is not None:
        new_tag_values = db.query(models.TagValue).filter(models.TagValue.id.in_(data.tagValueIds)).all()
        if len(new_tag_values) != len(set(data.tagValueIds)):
            raise HTTPException(status_code=400, detail="Some tagValueIds not found")
    else:
        new_tag_values = list(sched.tag_values)

    # Проверка required тегов
    required_tags = db.query(models.Tag).filter(models.Tag.required == True).all()
    if required_tags:
        tag_ids_present = {tv.tag_id for tv in new_tag_values}
        missing = [t.name for t in required_tags if t.id not in tag_ids_present]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required tags: {', '.join(missing)}")

    # Проверка уникальных ресурсов: пересечения по времени с другими событиями
    unique_tags = db.query(models.Tag).filter(models.Tag.unique_resource == True).all()
    if unique_tags and new_tag_values and not new_is_canceled:
        unique_tag_ids = {t.id for t in unique_tags}
        # значения по уникальным тегам
        uniq_value_ids = [tv.id for tv in new_tag_values if tv.tag_id in unique_tag_ids]
        if uniq_value_ids:
            existing = (
                db.query(models.Schedule)
                .join(models.Schedule.tag_values)
                .filter(
                    models.Schedule.id != sched.id,
                    models.TagValue.id.in_(uniq_value_ids),
                    ~(models.Schedule.date_to <= new_from),
                    ~(models.Schedule.date_from >= new_to),
                    models.Schedule.is_canceled == False,
                )
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail=f"Пересечение с событием \"{existing.title}\" (с {existing.date_from} по {existing.date_to})")

    # Применяем обновления
    sched.title = new_title
    sched.date_from = new_from
    sched.date_to = new_to
    sched.tag_values = new_tag_values
    sched.is_canceled = new_is_canceled
    sched.contact = new_contact
    db.commit()
    db.refresh(sched)
    # Сборка только изменившихся полей
    changes: list[str] = []
    if new_title != old_title:
        changes.append(f"title: {old_title} -> {new_title}")
    else:
        changes.append(f"title: {old_title}") # просто для того что бы понять в каком событии были изменения
    if new_from != old_from:
        changes.append(f"date_from: {old_from} -> {new_from}")
    if new_to != old_to:
        changes.append(f"date_to: {old_to} -> {new_to}")
    if new_is_canceled != old_is_canceled:
        changes.append(f"is_canceled: {old_is_canceled} -> {new_is_canceled}")
    if new_contact != old_contact:
        changes.append(f"contact: {old_contact} -> {new_contact}")
    new_tag_ids = [tv.id for tv in sched.tag_values]
    if sorted(new_tag_ids) != sorted(old_tag_ids):
        changes.append(f"tag_value_ids: {sorted(old_tag_ids)} -> {sorted(new_tag_ids)}")
    details = "; ".join(changes) if changes else None
    try:
        write_audit_log(db, user, "UPDATE", "schedules", sched.id, details=details)
    except Exception:
        pass
    return schemas.ScheduleOut(
        id=sched.id,
        title=sched.title,
        dateFrom=sched.date_from,
        dateTo=sched.date_to,
        tagValueIds=[tv.id for tv in sched.tag_values],
        isCanceled=sched.is_canceled,
        contact=sched.contact,
    )


@router.delete("/{id}", status_code=204)
def delete_schedule(id: int, db: Session = Depends(get_db), user: str | None = Depends(get_remote_user)):
    sched = db.get(models.Schedule, id)
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    del_details = f"title={sched.title}; from={sched.date_from}; to={sched.date_to}"
    db.delete(sched)
    db.commit()
    try:
        write_audit_log(db, user, "DELETE", "schedules", id, details=del_details)
    except Exception:
        pass
    return None


