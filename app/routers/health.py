from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from ..db import engine

router = APIRouter()


@router.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except OperationalError:
        return {"status": "degraded"}


