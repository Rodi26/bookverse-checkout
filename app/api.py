"""
Checkout API routes.

This module exposes a minimal order API for the demo checkout service.

Endpoints
---------
- POST `/orders` — Create an order with optional idempotency, validates stock
  and adjusts inventory on success; enqueues an `order.created` outbox event.
- GET `/orders/{order_id}` — Retrieve an order by identifier.
"""

from fastapi import APIRouter, Header, HTTPException
from bookverse_core.api.exceptions import (
    raise_validation_error, raise_not_found_error, raise_conflict_error,
    raise_idempotency_conflict, raise_insufficient_stock_error, raise_upstream_error
)
from typing import Optional
from sqlalchemy.orm import Session

from .database import session_scope
from .models import Order
from .schemas import CreateOrderRequest, OrderResponse, OrderItemResponse
from .services import create_order


router = APIRouter()


@router.post("/orders", response_model=OrderResponse, status_code=201)
def create_order_endpoint(payload: CreateOrderRequest, idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    """Create a new order.

    Parameters
    ----------
    payload: CreateOrderRequest
        The order request containing `userId` and a list of items
        with `bookId`, `qty`, and `unitPrice`.
    idempotency_key: Optional[str]
        Optional idempotency key provided via the `Idempotency-Key` header.
        When provided, duplicate requests with the same request hash will
        return the originally created order; requests with a different hash
        will be rejected with conflict.

    Returns
    -------
    OrderResponse
        The created order with computed totals and line items.

    Raises
    ------
    HTTPException
        409 if idempotency conflict or insufficient stock, 400 for validation
        errors, 502 for upstream inventory errors.
    """
    try:
        with session_scope() as session:
            order, items = create_order(session, payload, idempotency_key)
            return _to_response(order, items)
    except ValueError as ve:
        detail = str(ve)
        if detail.startswith("idempotency_conflict"):
            raise_idempotency_conflict("Order already exists with different parameters")
        if detail.startswith("insufficient_stock"):
            raise_insufficient_stock_error(detail)
        raise_validation_error(detail)
    except Exception as e:
        # Log the actual error for debugging instead of masking it
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in create_order_endpoint: {e}", exc_info=True)
        raise_upstream_error(f"Service error: {type(e).__name__}")


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):
    """Return an order by identifier.

    Parameters
    ----------
    order_id: str
        The order identifier to fetch.

    Returns
    -------
    OrderResponse
        The order and its items if found.

    Raises
    ------
    HTTPException
        404 if the order is not found.
    """
    with session_scope() as session:
        from typing import Optional as _Optional  # local alias to avoid top-level changes
        order: _Optional[Order] = session.get(Order, order_id)
        if not order:
            raise_not_found_error(f"Order {order_id} not found")
        return _to_response(order, order.items)


def _to_response(order: Order, items) -> OrderResponse:
    """Convert internal ORM models to API response schema."""
    return OrderResponse(
        orderId=order.id,
        status=order.status,
        total=order.total_amount,
        currency=order.currency,
        items=[OrderItemResponse(bookId=i.book_id, qty=i.quantity, unitPrice=i.unit_price, lineTotal=i.line_total) for i in items],
        createdAt=order.created_at.isoformat() if order.created_at else None,
    )


