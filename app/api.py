"""
API routes for Checkout.
"""

from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from .database import session_scope
from .models import Order
from .schemas import CreateOrderRequest, OrderResponse, OrderItemResponse
from .services import create_order


router = APIRouter()


@router.post("/orders", response_model=OrderResponse, status_code=201)
def create_order_endpoint(payload: CreateOrderRequest, idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    try:
        with session_scope() as session:
            order, items = create_order(session, payload, idempotency_key)
            return _to_response(order, items)
    except ValueError as ve:
        detail = str(ve)
        if detail.startswith("idempotency_conflict"):
            raise HTTPException(status_code=409, detail="idempotency_conflict")
        if detail.startswith("insufficient_stock"):
            raise HTTPException(status_code=409, detail=detail)
        raise HTTPException(status_code=400, detail=detail)
    except Exception:
        raise HTTPException(status_code=502, detail="upstream_error")


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    with session_scope() as session:
        from typing import Optional as _Optional  # local alias to avoid top-level changes
        order: _Optional[Order] = session.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="not_found")
        return _to_response(order, order.items)


def _to_response(order: Order, items) -> OrderResponse:
    return OrderResponse(
        orderId=order.id,
        status=order.status,
        total=order.total_amount,
        currency=order.currency,
        items=[OrderItemResponse(bookId=i.book_id, qty=i.quantity, unitPrice=i.unit_price, lineTotal=i.line_total) for i in items],
        createdAt=order.created_at.isoformat() if order.created_at else None,
    )


