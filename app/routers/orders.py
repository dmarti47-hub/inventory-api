from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderRead
from app.services.order_service import create_order

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def place_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    return create_order(db=db, order_data=order_data)


@router.get("", response_model=list[OrderRead])
def list_orders(
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )

    if status_filter is not None:
        statement = statement.where(Order.status == status_filter)

    statement = statement.offset(skip).limit(limit)

    return db.scalars(statement).all()


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    statement = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )

    order = db.scalar(statement)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    return order
