from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..db import get_db, engine, Base
from .. import models, schemas
from ..utils import get_remote_user, write_audit_log


router = APIRouter(prefix="/clients", tags=["clients"])


@router.on_event("startup")
def _create_clients_table():
    """Создание таблицы clients при запуске (мягкая миграция)."""
    Base.metadata.create_all(bind=engine)


@router.get("", response_model=list[schemas.ClientOut])
def list_clients(
    search: str | None = Query(default=None, description="Поиск по имени"),
    db: Session = Depends(get_db)
):
    """Получить список клиентов с опциональным поиском по имени."""
    clients = db.query(models.Client).order_by(models.Client.name).all()
    if search:
        # Регистронезависимый поиск в Python (SQLite lower() не работает с кириллицей)
        search_lower = search.lower()
        clients = [c for c in clients if search_lower in c.name.lower()]
    return clients


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Получить клиента по ID."""
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("", response_model=schemas.ClientOut)
def create_client(
    data: schemas.ClientCreate,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Создать нового клиента."""
    client = models.Client(name=data.name)
    db.add(client)
    db.commit()
    db.refresh(client)
    try:
        write_audit_log(db, user, "CREATE", "clients", client.id, details=f"name={client.name}")
    except Exception:
        pass
    return client


@router.put("/{client_id}", response_model=schemas.ClientOut)
def update_client(
    client_id: int,
    data: schemas.ClientUpdate,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Обновить клиента."""
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    old_name = client.name
    if data.name is not None:
        client.name = data.name
    db.commit()
    db.refresh(client)
    changes = []
    if client.name != old_name:
        changes.append(f"name: {old_name} -> {client.name}")
    details = "; ".join(changes) if changes else None
    try:
        write_audit_log(db, user, "UPDATE", "clients", client.id, details=details)
    except Exception:
        pass
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Удалить клиента."""
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    del_details = f"name={client.name}"
    db.delete(client)
    db.commit()
    try:
        write_audit_log(db, user, "DELETE", "clients", client_id, details=del_details)
    except Exception:
        pass
    return None

