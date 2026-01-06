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


class ClientBase(BaseModel):
    name: str = Field(min_length=1)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)


class ClientOut(ClientBase):
    id: int

    class Config:
        from_attributes = True


# ============ Типы абонементов (шаблоны) ============

class SubscriptionTypeBase(BaseModel):
    name: str = Field(min_length=1)
    lessonsCount: int = Field(gt=0)
    durationDays: int = Field(gt=0)


class SubscriptionTypeCreate(SubscriptionTypeBase):
    pass


class SubscriptionTypeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    lessonsCount: Optional[int] = Field(default=None, gt=0)
    durationDays: Optional[int] = Field(default=None, gt=0)


class SubscriptionTypeOut(BaseModel):
    id: int
    name: str
    lessonsCount: int
    durationDays: int

    class Config:
        from_attributes = True


# ============ Покупки абонементов ============

class SubscriptionPurchaseBase(BaseModel):
    clientId: int
    lessonsCount: int = Field(gt=0)
    purchaseDate: str
    expiryDate: str
    comment: Optional[str] = None


class SubscriptionPurchaseCreate(SubscriptionPurchaseBase):
    pass


class SubscriptionPurchaseUpdate(BaseModel):
    lessonsCount: int = Field(gt=0)
    purchaseDate: str
    expiryDate: str
    comment: Optional[str] = None


class SubscriptionPurchaseOut(BaseModel):
    id: int
    clientId: int
    lessonsCount: int
    purchaseDate: str
    expiryDate: str
    comment: Optional[str] = None

    class Config:
        from_attributes = True


# ============ Расходы абонементов ============

class SubscriptionExpenseBase(BaseModel):
    clientId: int
    expenseDate: str
    comment: Optional[str] = None


class SubscriptionExpenseCreate(SubscriptionExpenseBase):
    pass


class SubscriptionExpenseOut(BaseModel):
    id: int
    clientId: int
    expenseDate: str
    comment: Optional[str] = None

    class Config:
        from_attributes = True


# ============ Баланс клиента ============

class ClientBalanceOut(BaseModel):
    clientId: int
    clientName: str
    totalPurchased: int  # Сумма всех купленных занятий
    totalSpent: int  # Сумма всех расходов
    balance: int  # Остаток занятий
    purchases: List[SubscriptionPurchaseOut]
    expenses: List[SubscriptionExpenseOut]

