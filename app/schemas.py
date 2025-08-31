"""
Pydantic schemas for Checkout API.
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class OrderItemRequest(BaseModel):
    bookId: str
    qty: int = Field(gt=0)
    unitPrice: Decimal = Field(ge=0)


class CreateOrderRequest(BaseModel):
    userId: str
    items: List[OrderItemRequest]


class OrderItemResponse(BaseModel):
    bookId: str
    qty: int
    unitPrice: Decimal
    lineTotal: Decimal


class OrderResponse(BaseModel):
    orderId: str
    status: str
    total: Decimal
    currency: str = "USD"
    items: List[OrderItemResponse]
    createdAt: Optional[str] = None


