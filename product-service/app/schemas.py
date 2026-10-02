from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from typing import Optional

# Universal validation criteria shared across actions
class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0.00, decimal_places=2)
    stock: int = Field(..., ge=0)

# Schema representing payloads sent to POST /products
class ProductCreate(ProductBase):
    pass

# Schema handling variations of inventory adjustments
class StockReduce(BaseModel):
    quantity: int = Field(..., ge=1, description="Number of items to deduct from warehouse stock")

# Explicit response validation format returned to consumers
class ProductResponse(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

