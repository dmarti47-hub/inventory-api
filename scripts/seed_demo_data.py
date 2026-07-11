from decimal import Decimal

from sqlalchemy import delete

from app.database import SessionLocal
from app.models.inventory import InventoryAdjustment
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order_service import create_order, update_order_status


def reset_database_data() -> None:
    with SessionLocal() as db:
        db.execute(delete(OrderItem))
        db.execute(delete(Order))
        db.execute(delete(InventoryAdjustment))
        db.execute(delete(Product))
        db.commit()


def create_products() -> dict[str, Product]:
    products = [
        Product(
            sku="LAPTOP-001",
            name="Business Laptop",
            description="Standard office laptop for employee workstations",
            quantity=25,
            price=Decimal("899.99"),
        ),
        Product(
            sku="MONITOR-001",
            name="27 Inch Monitor",
            description="External display for office setups",
            quantity=14,
            price=Decimal("249.99"),
        ),
        Product(
            sku="KEYBOARD-001",
            name="Mechanical Keyboard",
            description="Wired mechanical keyboard",
            quantity=8,
            price=Decimal("89.99"),
        ),
        Product(
            sku="MOUSE-001",
            name="Wireless Mouse",
            description="Wireless ergonomic mouse",
            quantity=4,
            price=Decimal("39.99"),
        ),
        Product(
            sku="DOCK-001",
            name="USB-C Docking Station",
            description="Docking station for laptops and external displays",
            quantity=2,
            price=Decimal("129.99"),
        ),
    ]

    with SessionLocal() as db:
        for product in products:
            db.add(product)

        db.commit()

        for product in products:
            db.refresh(product)

        return {product.sku: product for product in products}


def create_inventory_adjustments(products_by_sku: dict[str, Product]) -> None:
    adjustments = [
        InventoryAdjustment(
            product_id=products_by_sku["LAPTOP-001"].id,
            quantity_change=5,
            reason="Initial supplier restock",
        ),
        InventoryAdjustment(
            product_id=products_by_sku["MOUSE-001"].id,
            quantity_change=-1,
            reason="Damaged item removed from stock",
        ),
        InventoryAdjustment(
            product_id=products_by_sku["DOCK-001"].id,
            quantity_change=2,
            reason="Emergency restock for low inventory",
        ),
    ]

    with SessionLocal() as db:
        for adjustment in adjustments:
            db.add(adjustment)

        laptop = db.get(Product, products_by_sku["LAPTOP-001"].id)
        mouse = db.get(Product, products_by_sku["MOUSE-001"].id)
        dock = db.get(Product, products_by_sku["DOCK-001"].id)

        if laptop is not None:
            laptop.quantity += 5

        if mouse is not None:
            mouse.quantity -= 1

        if dock is not None:
            dock.quantity += 2

        db.commit()


def create_demo_orders(products_by_sku: dict[str, Product]) -> None:
    with SessionLocal() as db:
        pending_order = create_order(
            db=db,
            order_data=OrderCreate(
                customer_name="Jane Smith",
                items=[
                    OrderItemCreate(
                        product_id=products_by_sku["LAPTOP-001"].id,
                        quantity=1,
                    ),
                    OrderItemCreate(
                        product_id=products_by_sku["MOUSE-001"].id,
                        quantity=2,
                    ),
                ],
            ),
        )

        paid_order = create_order(
            db=db,
            order_data=OrderCreate(
                customer_name="Marcus Lee",
                items=[
                    OrderItemCreate(
                        product_id=products_by_sku["MONITOR-001"].id,
                        quantity=2,
                    ),
                    OrderItemCreate(
                        product_id=products_by_sku["KEYBOARD-001"].id,
                        quantity=2,
                    ),
                ],
            ),
        )

        shipped_order = create_order(
            db=db,
            order_data=OrderCreate(
                customer_name="Avery Johnson",
                items=[
                    OrderItemCreate(
                        product_id=products_by_sku["DOCK-001"].id,
                        quantity=1,
                    ),
                ],
            ),
        )

        canceled_order = create_order(
            db=db,
            order_data=OrderCreate(
                customer_name="Canceled Demo Customer",
                items=[
                    OrderItemCreate(
                        product_id=products_by_sku["KEYBOARD-001"].id,
                        quantity=1,
                    ),
                ],
            ),
        )

        update_order_status(db=db, order_id=paid_order.id, new_status="paid")

        update_order_status(db=db, order_id=shipped_order.id, new_status="paid")
        update_order_status(db=db, order_id=shipped_order.id, new_status="shipped")

        update_order_status(db=db, order_id=canceled_order.id, new_status="canceled")

        print(f"Created pending order ID: {pending_order.id}")
        print(f"Created paid order ID: {paid_order.id}")
        print(f"Created shipped order ID: {shipped_order.id}")
        print(f"Created canceled order ID: {canceled_order.id}")


def main() -> None:
    print("Resetting existing demo data...")
    reset_database_data()

    print("Creating products...")
    products_by_sku = create_products()

    print("Creating inventory adjustments...")
    create_inventory_adjustments(products_by_sku)

    print("Creating demo orders...")
    create_demo_orders(products_by_sku)

    print("Demo data loaded successfully.")


if __name__ == "__main__":
    main()