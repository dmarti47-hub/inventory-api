from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import InventoryAdjustment
from app.models.product import Product
from app.schemas.inventory import (
    InventoryAdjustmentCreate,
    InventoryAdjustmentRead,
    InventoryAdjustmentResult,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post(
    "/adjust",
    response_model=InventoryAdjustmentResult,
    status_code=status.HTTP_201_CREATED,
)
def adjust_inventory(
    adjustment_data: InventoryAdjustmentCreate,
    db: Session = Depends(get_db),
):
    statement = (
        select(Product)
        .where(Product.id == adjustment_data.product_id)
        .with_for_update()
    )

    product = db.scalar(statement)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot adjust inventory for an inactive product.",
        )

    previous_quantity = product.quantity
    new_quantity = previous_quantity + adjustment_data.quantity_change

    if new_quantity < 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory cannot go below zero.",
        )

    product.quantity = new_quantity

    adjustment = InventoryAdjustment(
        product_id=product.id,
        quantity_change=adjustment_data.quantity_change,
        reason=adjustment_data.reason,
    )

    db.add(adjustment)
    db.commit()
    db.refresh(adjustment)
    db.refresh(product)

    return InventoryAdjustmentResult(
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        previous_quantity=previous_quantity,
        new_quantity=product.quantity,
        adjustment=adjustment,
    )


@router.get("/adjustments", response_model=list[InventoryAdjustmentRead])
def list_inventory_adjustments(
    db: Session = Depends(get_db),
    product_id: int | None = Query(default=None, gt=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    statement = select(InventoryAdjustment).order_by(
        InventoryAdjustment.created_at.desc()
    )

    if product_id is not None:
        statement = statement.where(InventoryAdjustment.product_id == product_id)

    statement = statement.offset(skip).limit(limit)

    return db.scalars(statement).all()
