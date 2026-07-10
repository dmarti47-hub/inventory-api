from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.product import Product

REVENUE_STATUSES = ["paid", "shipped"]


def get_low_stock_products(db: Session, threshold: int) -> list[Product]:
    statement = (
        select(Product)
        .where(Product.is_active.is_(True))
        .where(Product.quantity <= threshold)
        .order_by(Product.quantity.asc(), Product.name.asc())
    )

    return db.scalars(statement).all()


def get_revenue_summary(db: Session) -> dict:
    statement = select(
        func.count(Order.id),
        func.sum(Order.total_amount),
    ).where(Order.status.in_(REVENUE_STATUSES))

    order_count, total_revenue = db.execute(statement).one()

    if total_revenue is None:
        total_revenue = Decimal("0.00")

    if order_count == 0:
        average_order_value = Decimal("0.00")
    else:
        average_order_value = total_revenue / order_count

    return {
        "paid_or_shipped_order_count": order_count,
        "total_revenue": total_revenue,
        "average_order_value": average_order_value,
    }
