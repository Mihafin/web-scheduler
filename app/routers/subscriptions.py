from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db import get_db, engine, Base
from .. import models, schemas
from ..utils import get_remote_user, write_audit_log


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.on_event("startup")
def _create_subscriptions_tables():
    """Создание таблиц для абонементов при запуске."""
    Base.metadata.create_all(bind=engine)


# ============ Покупки (приходы) ============

@router.get("/purchases", response_model=list[schemas.SubscriptionPurchaseOut])
def list_purchases(
    client_id: int | None = Query(default=None, description="Фильтр по клиенту"),
    db: Session = Depends(get_db)
):
    """Получить список покупок абонементов."""
    q = db.query(models.SubscriptionPurchase)
    if client_id:
        q = q.filter(models.SubscriptionPurchase.client_id == client_id)
    purchases = q.order_by(models.SubscriptionPurchase.purchase_date.desc()).all()
    return [
        schemas.SubscriptionPurchaseOut(
            id=p.id,
            clientId=p.client_id,
            lessonsCount=p.lessons_count,
            purchaseDate=p.purchase_date,
            expiryDate=p.expiry_date,
            comment=p.comment
        )
        for p in purchases
    ]


@router.post("/purchases", response_model=schemas.SubscriptionPurchaseOut)
def create_purchase(
    data: schemas.SubscriptionPurchaseCreate,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Создать новую покупку абонемента."""
    # Проверяем существование клиента
    client = db.get(models.Client, data.clientId)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    purchase = models.SubscriptionPurchase(
        client_id=data.clientId,
        lessons_count=data.lessonsCount,
        purchase_date=data.purchaseDate,
        expiry_date=data.expiryDate,
        comment=data.comment
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    
    try:
        write_audit_log(db, user, "CREATE", "subscription_purchases", purchase.id,
                        details=f"client={client.name}; lessons={purchase.lessons_count}; comment={purchase.comment}")
    except Exception:
        pass
    
    return schemas.SubscriptionPurchaseOut(
        id=purchase.id,
        clientId=purchase.client_id,
        lessonsCount=purchase.lessons_count,
        purchaseDate=purchase.purchase_date,
        expiryDate=purchase.expiry_date,
        comment=purchase.comment
    )


@router.put("/purchases/{purchase_id}", response_model=schemas.SubscriptionPurchaseOut)
def update_purchase(
    purchase_id: int,
    data: schemas.SubscriptionPurchaseUpdate,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Обновить покупку абонемента."""
    purchase = db.get(models.SubscriptionPurchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    old_values = f"lessons={purchase.lessons_count}; date={purchase.purchase_date}; expiry={purchase.expiry_date}; comment={purchase.comment}"
    
    purchase.lessons_count = data.lessonsCount
    purchase.purchase_date = data.purchaseDate
    purchase.expiry_date = data.expiryDate
    purchase.comment = data.comment
    
    db.commit()
    db.refresh(purchase)
    
    new_values = f"lessons={purchase.lessons_count}; date={purchase.purchase_date}; expiry={purchase.expiry_date}; comment={purchase.comment}"
    
    try:
        client = db.get(models.Client, purchase.client_id)
        client_name = client.name if client else "?"
        write_audit_log(db, user, "UPDATE", "subscription_purchases", purchase_id,
                        details=f"client={client_name}; old=[{old_values}]; new=[{new_values}]")
    except Exception:
        pass
    
    return schemas.SubscriptionPurchaseOut(
        id=purchase.id,
        clientId=purchase.client_id,
        lessonsCount=purchase.lessons_count,
        purchaseDate=purchase.purchase_date,
        expiryDate=purchase.expiry_date,
        comment=purchase.comment
    )


@router.delete("/purchases/{purchase_id}", status_code=204)
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Удалить покупку абонемента."""
    purchase = db.get(models.SubscriptionPurchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    client = db.get(models.Client, purchase.client_id)
    client_name = client.name if client else "?"
    del_details = f"client={client_name}; lessons={purchase.lessons_count}; comment={purchase.comment}"
    
    db.delete(purchase)
    db.commit()
    
    try:
        write_audit_log(db, user, "DELETE", "subscription_purchases", purchase_id, details=del_details)
    except Exception:
        pass
    
    return None


# ============ Расходы ============

@router.get("/expenses", response_model=list[schemas.SubscriptionExpenseOut])
def list_expenses(
    client_id: int | None = Query(default=None, description="Фильтр по клиенту"),
    db: Session = Depends(get_db)
):
    """Получить список расходов."""
    q = db.query(models.SubscriptionExpense)
    if client_id:
        q = q.filter(models.SubscriptionExpense.client_id == client_id)
    expenses = q.order_by(models.SubscriptionExpense.expense_date.desc()).all()
    return [
        schemas.SubscriptionExpenseOut(
            id=e.id,
            clientId=e.client_id,
            expenseDate=e.expense_date,
            comment=e.comment
        )
        for e in expenses
    ]


@router.post("/expenses", response_model=schemas.SubscriptionExpenseOut)
def create_expense(
    data: schemas.SubscriptionExpenseCreate,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Создать новый расход (списание 1 занятия)."""
    # Проверяем существование клиента
    client = db.get(models.Client, data.clientId)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    expense = models.SubscriptionExpense(
        client_id=data.clientId,
        expense_date=data.expenseDate,
        comment=data.comment
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    try:
        write_audit_log(db, user, "CREATE", "subscription_expenses", expense.id,
                        details=f"client={client.name}; date={expense.expense_date}; comment={expense.comment}")
    except Exception:
        pass
    
    return schemas.SubscriptionExpenseOut(
        id=expense.id,
        clientId=expense.client_id,
        expenseDate=expense.expense_date,
        comment=expense.comment
    )


@router.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    user: str | None = Depends(get_remote_user)
):
    """Удалить расход."""
    expense = db.get(models.SubscriptionExpense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    client = db.get(models.Client, expense.client_id)
    client_name = client.name if client else "?"
    del_details = f"client={client_name}; date={expense.expense_date}; comment={expense.comment}"
    
    db.delete(expense)
    db.commit()
    
    try:
        write_audit_log(db, user, "DELETE", "subscription_expenses", expense_id, details=del_details)
    except Exception:
        pass
    
    return None


# ============ Баланс клиента ============

@router.get("/balance/{client_id}", response_model=schemas.ClientBalanceOut)
def get_client_balance(client_id: int, db: Session = Depends(get_db)):
    """Получить баланс клиента (остаток занятий)."""
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Сумма всех купленных занятий
    total_purchased = db.query(func.coalesce(func.sum(models.SubscriptionPurchase.lessons_count), 0)).filter(
        models.SubscriptionPurchase.client_id == client_id
    ).scalar()
    
    # Количество расходов (каждый = 1 занятие)
    total_spent = db.query(func.count(models.SubscriptionExpense.id)).filter(
        models.SubscriptionExpense.client_id == client_id
    ).scalar()
    
    # Список покупок
    purchases = db.query(models.SubscriptionPurchase).filter(
        models.SubscriptionPurchase.client_id == client_id
    ).order_by(models.SubscriptionPurchase.purchase_date.desc()).all()
    
    # Список расходов
    expenses = db.query(models.SubscriptionExpense).filter(
        models.SubscriptionExpense.client_id == client_id
    ).order_by(models.SubscriptionExpense.expense_date.desc()).all()
    
    return schemas.ClientBalanceOut(
        clientId=client.id,
        clientName=client.name,
        totalPurchased=int(total_purchased),
        totalSpent=int(total_spent),
        balance=int(total_purchased) - int(total_spent),
        purchases=[
            schemas.SubscriptionPurchaseOut(
                id=p.id,
                clientId=p.client_id,
                lessonsCount=p.lessons_count,
                purchaseDate=p.purchase_date,
                expiryDate=p.expiry_date,
                comment=p.comment
            )
            for p in purchases
        ],
        expenses=[
            schemas.SubscriptionExpenseOut(
                id=e.id,
                clientId=e.client_id,
                expenseDate=e.expense_date,
                comment=e.comment
            )
            for e in expenses
        ]
    )

