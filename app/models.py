from __future__ import annotations

from sqlalchemy import Integer, String, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    unique_resource: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    values: Mapped[list[TagValue]] = relationship("TagValue", back_populates="tag", cascade="all, delete-orphan")


class TagValue(Base):
    __tablename__ = "tag_values"
    __table_args__ = (
        UniqueConstraint("tag_id", "value", name="uq_tag_value_per_tag"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), nullable=False)
    value: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str | None] = mapped_column(String, nullable=True)  # HEX цвет для значения

    tag: Mapped[Tag] = relationship("Tag", back_populates="values")
    schedules: Mapped[list[Schedule]] = relationship(
        secondary="schedule_tag_values",
        back_populates="tag_values",
    )


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    date_from: Mapped[str] = mapped_column(String, nullable=False)  # ISO-8601
    date_to: Mapped[str] = mapped_column(String, nullable=False)
    is_canceled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    contact: Mapped[str | None] = mapped_column(String, nullable=True)

    tag_values: Mapped[list[TagValue]] = relationship(
        secondary="schedule_tag_values",
        back_populates="schedules",
    )


class ScheduleTagValue(Base):
    __tablename__ = "schedule_tag_values"

    schedule_id: Mapped[int] = mapped_column(ForeignKey("schedules.id", ondelete="CASCADE"), primary_key=True)
    tag_value_id: Mapped[int] = mapped_column(ForeignKey("tag_values.id", ondelete="CASCADE"), primary_key=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[str] = mapped_column(String, nullable=False)  # ISO-8601 UTC timestamp
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)  # CREATE/UPDATE/DELETE
    entity: Mapped[str] = mapped_column(String, nullable=False)  # table/model name
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[str | None] = mapped_column(String, nullable=True)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    purchases: Mapped[list[SubscriptionPurchase]] = relationship("SubscriptionPurchase", back_populates="client", cascade="all, delete-orphan")
    expenses: Mapped[list[SubscriptionExpense]] = relationship("SubscriptionExpense", back_populates="client", cascade="all, delete-orphan")


class SubscriptionType(Base):
    """Шаблоны/типы абонементов (стартерпак, мультипас и т.д.)"""
    __tablename__ = "subscription_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    lessons_count: Mapped[int] = mapped_column(Integer, nullable=False)  # Количество занятий
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)  # Срок действия в днях


class SubscriptionPurchase(Base):
    """Покупка (приход) абонемента"""
    __tablename__ = "subscription_purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    lessons_count: Mapped[int] = mapped_column(Integer, nullable=False)  # Количество купленных занятий
    purchase_date: Mapped[str] = mapped_column(String, nullable=False)  # Дата покупки (ISO-8601)
    expiry_date: Mapped[str] = mapped_column(String, nullable=False)  # Дата завершения действия (ISO-8601)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)  # Комментарий

    client: Mapped[Client] = relationship("Client", back_populates="purchases")


class SubscriptionExpense(Base):
    """Расход (трата) занятия из абонемента"""
    __tablename__ = "subscription_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    expense_date: Mapped[str] = mapped_column(String, nullable=False)  # Дата расхода (ISO-8601)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)  # Комментарий

    client: Mapped[Client] = relationship("Client", back_populates="expenses")

