from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional


class TagBase(BaseModel):
    name: str = Field(min_length=1)
    required: bool = False
    unique_resource: bool = False


class TagCreate(TagBase):
    pass


class TagUpdate(TagBase):
    pass


class TagOut(TagBase):
    id: int

    class Config:
        from_attributes = True


class TagValueBase(BaseModel):
    value: str = Field(min_length=1)
    color: str | None = None


class TagValueCreate(TagValueBase):
    pass


class TagValueUpdate(TagValueBase):
    pass


class TagValueOut(TagValueBase):
    id: int
    tag_id: int

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    title: str
    dateFrom: str
    dateTo: str
    tagValueIds: Optional[List[int]] = None
    contact: Optional[str] = None


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    title: Optional[str] = None
    dateFrom: Optional[str] = None
    dateTo: Optional[str] = None
    tagValueIds: Optional[List[int]] = None
    isCanceled: Optional[bool] = None
    contact: Optional[str] = None


class ScheduleOut(BaseModel):
    id: int
    title: str
    dateFrom: str
    dateTo: str
    tagValueIds: List[int]
    isCanceled: bool
    contact: Optional[str] = None

    class Config:
        from_attributes = True


class AuditEntryOut(BaseModel):
    id: int
    ts: str
    username: str | None
    action: str
    entity: str
    entityId: int | None
    details: str | None = None

