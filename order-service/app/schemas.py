from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    total: Decimal
    status: str
    created_at: datetime
