"""
Business logic for Checkout.
"""

import hashlib
from decimal import Decimal
from typing import List, Tuple

from sqlalchemy.orm import Session

from .models import Order, OrderItem, IdempotencyKey, OutboxEvent
from .schemas import CreateOrderRequest
from .inventory_client import InventoryClient, InventoryError


def stable_request_hash(data: CreateOrderRequest) -> str:
    # JSON-stable hash based on sorted fields
    raw = f"{data.userId}|" + ",".join(
        f"{i.bookId}:{i.qty}:{i.unitPrice}" for i in sorted(data.items, key=lambda x: (x.bookId, x.qty, x.unitPrice))
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def upsert_idempotency(session: Session, key: str, request_hash: str) -> Tuple[str, str]:
    entry = session.get(IdempotencyKey, key)
    if entry is None:
        # create a stub order id early
        order = Order(user_id="", status="PENDING")
        session.add(order)
        session.flush()
        session.add(IdempotencyKey(key=key, order_id=order.id, request_hash=request_hash))
        return ("proceed", order.id)
    if entry.request_hash != request_hash:
        return ("conflict", entry.order_id)
    return ("replay", entry.order_id)


def calculate_totals(items: List[Tuple[Decimal, int]]) -> Decimal:
    total = Decimal("0")
    for price, qty in items:
        total += (price * qty)
    return total.quantize(Decimal("0.01"))


def create_order(session: Session, req: CreateOrderRequest, idempotency_key: str | None) -> Tuple[Order, List[OrderItem]]:
    inv = InventoryClient()
    req_hash = stable_request_hash(req)
    if idempotency_key:
        decision, order_id = upsert_idempotency(session, idempotency_key, req_hash)
        if decision == "conflict":
            raise ValueError("idempotency_conflict")
        if decision == "replay":
            order = session.get(Order, order_id)
            return order, order.items
        order = session.get(Order, order_id)
    else:
        order = Order(user_id=req.userId, status="PENDING")
        session.add(order)
        session.flush()

    # validation
    if not req.items:
        raise ValueError("validation_error: empty items")

    # Pre-check stock
    failures = []
    for item in req.items:
        inv_data = inv.get_inventory(item.bookId) or {}
        available = inv_data.get("inventory", {}).get("quantity_available", 0)
        if available < item.qty:
            failures.append({"bookId": item.bookId, "available": available, "requested": item.qty})
    if failures:
        raise ValueError(f"insufficient_stock:{failures}")

    # Create order items and adjust inventory (with compensation on failure)
    created_items: List[OrderItem] = []
    try:
        for item in req.items:
            inv.adjust(item.bookId, -int(item.qty), notes=f"order:{order.id}")
            line_total = (item.unitPrice * item.qty).quantize(Decimal("0.01"))
            oi = OrderItem(
                order_id=order.id,
                book_id=item.bookId,
                quantity=int(item.qty),
                unit_price=item.unitPrice,
                line_total=line_total,
            )
            session.add(oi)
            created_items.append(oi)
        # compute totals
        total = calculate_totals([(i.unitPrice, i.qty) for i in req.items])
        order.user_id = req.userId
        order.total_amount = total
        order.status = "CONFIRMED"
        session.flush()
        # enqueue outbox event
        session.add(OutboxEvent(type="order.created", payload={
            "orderId": order.id,
            "userId": req.userId,
            "total": float(total),
            "items": [{"bookId": it.bookId, "qty": it.qty} for it in req.items],
        }))
        return order, created_items
    except Exception:
        # Compensation
        for it in req.items:
            try:
                inv.adjust(it.bookId, int(it.qty), notes=f"compensate:{order.id}")
            except InventoryError:
                # Log-only in demo; in real system, raise alert
                pass
        order.status = "CANCELLED"
        session.flush()
        raise


