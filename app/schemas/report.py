from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class LowStockProduct(BaseModel):
    id: int
    sku: str
    name: str
    quantity: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class RevenueSummary(BaseModel):
    paid_or_shipped_order_count: int
    total_revenue: Decimal
    average_order_value: Decimal
