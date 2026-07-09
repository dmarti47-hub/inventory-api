from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.order import Order
from app.models.product import Product
from app.schemas.report import LowStockProduct, RevenueSummary
from app.services.csv_service import create_csv_response
from app.services.report_service import get_low_stock_products, get_revenue_summary

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/low-stock", response_model=list[LowStockProduct])
def low_stock_report(
    threshold: int = Query(default=5, ge=0),
    db: Session = Depends(get_db),
):
    return get_low_stock_products(db=db, threshold=threshold)


@router.get("/revenue-summary", response_model=RevenueSummary)
def revenue_summary(db: Session = Depends(get_db)):
    return get_revenue_summary(db=db)


@router.get("/products.csv", response_class=StreamingResponse)
def export_products_csv(
    include_inactive: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    statement = select(Product).order_by(Product.name.asc())

    if not include_inactive:
        statement = statement.where(Product.is_active.is_(True))

    products = db.scalars(statement).all()

    rows = [
        {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "description": product.description or "",
            "quantity": product.quantity,
            "price": str(product.price),
            "is_active": product.is_active,
        }
        for product in products
    ]

    return create_csv_response(
        filename="products.csv",
        fieldnames=[
            "id",
            "sku",
            "name",
            "description",
            "quantity",
            "price",
            "is_active",
        ],
        rows=rows,
    )


@router.get("/low-stock.csv", response_class=StreamingResponse)
def export_low_stock_csv(
    threshold: int = Query(default=5, ge=0),
    db: Session = Depends(get_db),
):
    products = get_low_stock_products(db=db, threshold=threshold)

    rows = [
        {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "quantity": product.quantity,
            "price": str(product.price),
        }
        for product in products
    ]

    return create_csv_response(
        filename="low_stock_products.csv",
        fieldnames=[
            "id",
            "sku",
            "name",
            "quantity",
            "price",
        ],
        rows=rows,
    )


@router.get("/orders.csv", response_class=StreamingResponse)
def export_orders_csv(
    status_filter: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )

    if status_filter is not None:
        statement = statement.where(Order.status == status_filter)

    orders = db.scalars(statement).all()

    rows = [
        {
            "id": order.id,
            "customer_name": order.customer_name,
            "status": order.status,
            "total_amount": str(order.total_amount),
            "item_count": sum(item.quantity for item in order.items),
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
        }
        for order in orders
    ]

    return create_csv_response(
        filename="orders.csv",
        fieldnames=[
            "id",
            "customer_name",
            "status",
            "total_amount",
            "item_count",
            "created_at",
            "updated_at",
        ],
        rows=rows,
    )