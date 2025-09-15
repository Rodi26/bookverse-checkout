"""
Checkout API routes.

MIGRATION SUCCESS: Enhanced with bookverse-core pagination and logging!

This module exposes the order API for the BookVerse checkout service.

Endpoints
---------
- GET `/orders` — List orders with pagination support (NEW - bookverse-core integration)
- POST `/orders` — Create an order with optional idempotency, validates stock
  and adjusts inventory on success; enqueues an `order.created` outbox event.
- GET `/orders/{order_id}` — Retrieve an order by identifier.

Features
--------
✅ Bookverse-core pagination support
✅ Standardized error handling  
✅ Request/response logging
✅ Consistent API patterns
"""

from fastapi import APIRouter, Header, HTTPException, Depends
from bookverse_core.api.exceptions import (
    raise_validation_error, raise_not_found_error, raise_conflict_error,
    raise_idempotency_conflict, raise_insufficient_stock_error, raise_upstream_error
)
from bookverse_core.api.responses import (
    SuccessResponse, 
    PaginatedResponse,
    create_success_response,
    create_paginated_response
)
from bookverse_core.api.pagination import (
    PaginationParams,
    create_pagination_params,
    create_pagination_meta
)
from bookverse_core.utils.logging import get_logger
from typing import Optional, List
from sqlalchemy.orm import Session

from .database import session_scope
from .models import Order
from .schemas import CreateOrderRequest, OrderResponse, OrderItemResponse
from .services import create_order

# Get logger for this module
logger = get_logger(__name__)

router = APIRouter()


@router.get("/orders", response_model=PaginatedResponse[OrderResponse])
def list_orders(
    pagination: PaginationParams = Depends(create_pagination_params),
    user_id: Optional[str] = None
):
    """List orders with pagination support.
    
    This endpoint demonstrates bookverse-core pagination integration.
    
    Parameters
    ----------
    pagination: PaginationParams
        Pagination parameters (page, size) automatically parsed from query params
    user_id: Optional[str]
        Filter orders by user ID if provided
    
    Returns
    -------
    PaginatedResponse[OrderResponse]
        Paginated list of orders with metadata
    """
    logger.info(f"📋 Listing orders with pagination: page={pagination.page}, size={pagination.size}")
    
    try:
        with session_scope() as session:
            # Build query
            query = session.query(Order)
            if user_id:
                query = query.filter(Order.user_id == user_id)
                logger.debug(f"🔍 Filtering orders by user_id: {user_id}")
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (pagination.page - 1) * pagination.size
            orders = query.offset(offset).limit(pagination.size).all()
            
            # Convert to response objects
            order_responses = []
            for order in orders:
                # Get order items for each order
                items = session.query(order.items).all() if hasattr(order, 'items') else []
                order_responses.append(_to_response(order, items))
            
            # Create pagination metadata
            pagination_meta = create_pagination_meta(
                page=pagination.page,
                size=pagination.size,
                total_count=total_count
            )
            
            logger.info(f"✅ Retrieved {len(order_responses)} orders (page {pagination.page}/{pagination_meta.total_pages})")
            
            return create_paginated_response(
                data=order_responses,
                pagination=pagination_meta,
                message=f"Retrieved {len(order_responses)} orders"
            )
            
    except Exception as e:
        logger.error(f"❌ Failed to list orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve orders")


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


