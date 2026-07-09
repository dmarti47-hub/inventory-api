from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InventoryAdjustmentCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity_change: int
    reason: str | None = Field(default=None, max_length=255)

    @field_validator("quantity_change")
    @classmethod
    def quantity_change_cannot_be_zero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Quantity change cannot be zero.")
        return value


class InventoryAdjustmentRead(BaseModel):
    id: int
    product_id: int
    quantity_change: int
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryAdjustmentResult(BaseModel):
    product_id: int
    sku: str
    name: str
    previous_quantity: int
    new_quantity: int
    adjustment: InventoryAdjustmentRead
