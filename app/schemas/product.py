from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    quantity: int = Field(default=0, ge=0)
    price: Decimal = Field(..., gt=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    quantity: int | None = Field(default=None, ge=0)
    price: Decimal | None = Field(default=None, gt=0)
    is_active: bool | None = None


class ProductRead(BaseModel):
    id: int
    sku: str
    name: str
    description: str | None
    quantity: int
    price: Decimal
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
