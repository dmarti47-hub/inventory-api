from collections import defaultdict
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate

VALID_STATUS_TRANSITIONS = {
    "pending": {"paid", "canceled"},
    "paid": {"shipped", "canceled"},
    "shipped": set(),
    "canceled": set(),
}


def create_order(db: Session, order_data: OrderCreate) -> Order:
    quantity_by_product_id: dict[int, int] = defaultdict(int)

    for item in order_data.items:
        quantity_by_product_id[item.product_id] += item.quantity

    product_ids = list(quantity_by_product_id.keys())

    statement = select(Product).where(Product.id.in_(product_ids)).with_for_update()

    products = db.scalars(statement).all()
    products_by_id = {product.id: product for product in products}

    missing_product_ids = sorted(set(product_ids) - set(products_by_id.keys()))

    if missing_product_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product IDs not found: {missing_product_ids}",
        )

    for product_id, requested_quantity in quantity_by_product_id.items():
        product = products_by_id[product_id]

        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {product_id} is inactive.",
            )

        if product.quantity < requested_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for product {product_id}. "
                    f"Available: {product.quantity}, requested: {requested_quantity}."
                ),
            )

    order = Order(
        customer_name=order_data.customer_name,
        status="pending",
        total_amount=Decimal("0.00"),
    )

    total_amount = Decimal("0.00")

    for product_id, requested_quantity in quantity_by_product_id.items():
        product = products_by_id[product_id]

        unit_price = product.price
        line_total = unit_price * requested_quantity

        product.quantity -= requested_quantity
        total_amount += line_total

        order.items.append(
            OrderItem(
                product_id=product.id,
                quantity=requested_quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    order.total_amount = total_amount

    db.add(order)
    db.commit()

    return _get_order_with_items(db=db, order_id=order.id)


def update_order_status(db: Session, order_id: int, new_status: str) -> Order:
    order = _get_order_with_items_for_update(db=db, order_id=order_id)

    if new_status == order.status:
        return order

    allowed_next_statuses = VALID_STATUS_TRANSITIONS[order.status]

    if new_status not in allowed_next_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot change order status from '{order.status}' to '{new_status}'."
            ),
        )

    if new_status == "canceled":
        _restore_stock_for_order(db=db, order=order)

    order.status = new_status

    db.commit()

    return _get_order_with_items(db=db, order_id=order.id)


def _get_order_with_items(db: Session, order_id: int) -> Order:
    statement = (
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )

    order = db.scalar(statement)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    return order


def _get_order_with_items_for_update(db: Session, order_id: int) -> Order:
    statement = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
        .with_for_update()
    )

    order = db.scalar(statement)

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )

    return order


def _restore_stock_for_order(db: Session, order: Order) -> None:
    product_ids = [item.product_id for item in order.items]

    statement = select(Product).where(Product.id.in_(product_ids)).with_for_update()

    products = db.scalars(statement).all()
    products_by_id = {product.id: product for product in products}

    for item in order.items:
        product = products_by_id.get(item.product_id)

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} no longer exists.",
            )

        product.quantity += item.quantity
