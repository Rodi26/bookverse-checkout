




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

logger = get_logger(__name__)

router = APIRouter()


@router.get("/orders", response_model=PaginatedResponse[OrderResponse])
def list_orders(
    pagination: PaginationParams = Depends(create_pagination_params),
    user_id: Optional[str] = None
):
    
    
    
    logger.info(f"📋 Listing orders with pagination: page={pagination.page}, size={pagination.size}")
    
    try:
        with session_scope() as session:
            query = session.query(Order)
            if user_id:
                query = query.filter(Order.user_id == user_id)
                logger.debug(f"🔍 Filtering orders by user_id: {user_id}")
            
            total_count = query.count()
            
            offset = (pagination.page - 1) * pagination.size
            orders = query.offset(offset).limit(pagination.size).all()
            
            order_responses = []
            for order in orders:
                items = session.query(order.items).all() if hasattr(order, 'items') else []
                order_responses.append(_to_response(order, items))
            
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
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in create_order_endpoint: {e}", exc_info=True)
        raise_upstream_error(f"Service error: {type(e).__name__}")


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str):



    with session_scope() as session:
        from typing import Optional as _Optional
        order: _Optional[Order] = session.get(Order, order_id)
        if not order:
            raise_not_found_error(f"Order {order_id} not found")
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


