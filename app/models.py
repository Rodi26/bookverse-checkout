"""
ORM models for Checkout.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4

from .database import Base


def _uuid() -> str:
    return str(uuid4())


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String, nullable=False, default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, default=_uuid)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)
    book_id = Column(String, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key = Column(String, primary_key=True)
    order_id = Column(String, nullable=False, index=True)
    request_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("key"),
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(String, primary_key=True, default=_uuid)
    type = Column(String, nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


