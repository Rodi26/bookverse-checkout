
"""
BookVerse Checkout Service - Database Models

This module defines SQLAlchemy ORM models for the checkout service database,
implementing sophisticated order management, idempotency handling, and event
sourcing patterns for reliable e-commerce transaction processing.

🏗️ Database Schema Architecture:
    - Order: Core order entity with status tracking and financial data
    - OrderItem: Line items with product details and pricing
    - IdempotencyKey: Duplicate request prevention for API safety
    - OutboxEvent: Event sourcing for reliable message publishing

🔧 Key Design Patterns:
    - UUID primary keys for distributed system compatibility
    - Optimistic concurrency with timestamps
    - Decimal precision for financial calculations
    - Foreign key relationships with cascade deletes
    - Indexing for query performance optimization
    - Event sourcing with outbox pattern for reliability

📊 Business Logic Implementation:
    - Order lifecycle management with status transitions
    - Financial calculations with currency support
    - Inventory reservation and confirmation workflows
    - Idempotency for safe operation retries
    - Audit trail with creation and modification timestamps

Authors: BookVerse Platform Team
Version: 1.0.0
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4

from .database import Base


def _uuid() -> str:
    """
    Generate a UUID string for use as primary keys.
    
    This function provides a consistent way to generate UUID strings for
    database primary keys across all models. UUIDs are used instead of
    auto-incrementing integers to support distributed systems and avoid
    ID conflicts when merging data from multiple sources.
    
    Returns:
        str: UUID4 string suitable for use as a primary key
        
    Example:
        ```python
        # Used automatically when creating model instances
        order = Order(user_id="user123", total_amount=29.99)
        print(order.id)  # "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        ```
    """
    return str(uuid4())


class Order(Base):
    """
    Core order entity representing customer purchase transactions.
    
    The Order model serves as the central entity for managing customer purchases
    in the BookVerse checkout system. It tracks the complete lifecycle of an
    order from creation through completion, including financial details,
    status transitions, and relationships to order items.
    
    🎯 Business Purpose:
        - Represent customer purchase transactions with complete audit trail
        - Track order status through the fulfillment pipeline
        - Maintain financial integrity with decimal precision pricing
        - Enable order management and customer service operations
        - Support inventory reservation and payment processing workflows
    
    💰 Financial Management:
        - Decimal precision for accurate monetary calculations
        - Multi-currency support for international transactions
        - Total amount calculation including taxes and shipping
        - Financial audit trail with creation and update timestamps
        - Integration with payment gateway transaction records
    
    🔄 Status Lifecycle:
        The order progresses through defined states:
        - PENDING: Initial state after order creation
        - RESERVED: Inventory items successfully reserved
        - PROCESSING_PAYMENT: Payment gateway processing in progress
        - PAID: Payment confirmed, ready for fulfillment
        - FULFILLING: Order being prepared for shipment
        - COMPLETED: Order successfully delivered
        - CANCELLED: Order cancelled (payment failed or customer request)
        - REFUNDED: Order refunded after completion
    
    📊 Data Structure:
        Identification:
        - id: UUID primary key for distributed system compatibility
        - user_id: Reference to customer account (external system)
        
        Financial Data:
        - total_amount: Order total with decimal precision (10,2)
        - currency: Three-letter currency code (ISO 4217)
        
        Status Tracking:
        - status: Current order state for workflow management
        - created_at: Order creation timestamp for audit trail
        - updated_at: Last modification timestamp for change tracking
        
        Relationships:
        - items: One-to-many relationship with OrderItem entities
    
    🛠️ Usage Examples:
        Creating a new order:
        ```python
        order = Order(
            user_id="customer123",
            total_amount=Decimal("45.98"),
            currency="USD",
            status="PENDING"
        )
        
        # Add order items
        order.items.append(OrderItem(
            book_id="book456",
            quantity=2,
            unit_price=Decimal("19.99"),
            line_total=Decimal("39.98")
        ))
        ```
        
        Querying orders with items:
        ```python
        # Load order with all items
        order = session.query(Order).options(
            joinedload(Order.items)
        ).filter_by(id=order_id).first()
        
        # Calculate totals
        calculated_total = sum(item.line_total for item in order.items)
        ```
        
        Status transition:
        ```python
        # Update order status with timestamp
        order.status = "PAID"
        order.updated_at = datetime.utcnow()
        session.commit()
        ```
    
    🔒 Data Integrity:
        - UUID primary keys prevent ID conflicts
        - Non-null constraints ensure data completeness
        - Decimal type prevents floating-point precision errors
        - Foreign key constraints maintain referential integrity
        - Cascade deletes ensure cleanup of dependent records
    
    📈 Performance Considerations:
        - User ID indexed for customer order lookups
        - Status field enables efficient status-based queries
        - Timestamps support time-based reporting and analytics
        - Relationship loading can be optimized with joinedload
    
    🔗 Integration Points:
        - User Service: Customer account verification
        - Inventory Service: Product availability and reservations
        - Payment Service: Transaction processing and confirmation
        - Shipping Service: Fulfillment and delivery tracking
        - Analytics Service: Order metrics and reporting
    
    Version: 1.0.0
    Table: orders
    """
    __tablename__ = "orders"

    # Primary identification with UUID for distributed systems
    id = Column(String, primary_key=True, default=_uuid)
    
    # Customer reference (links to external user service)
    user_id = Column(String, nullable=False, index=True)  # Indexed for customer queries
    
    # Order status for workflow management
    status = Column(String, nullable=False, default="PENDING")
    
    # Financial data with decimal precision for accuracy
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)  # Precise decimal arithmetic
    currency = Column(String, nullable=False, default="USD")          # ISO 4217 currency codes
    
    # Audit trail timestamps for order lifecycle tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One-to-many relationship with order items (cascade delete for cleanup)
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation for debugging and logging."""
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status}, total={self.total_amount})>"


class OrderItem(Base):
    """
    Individual line items within customer orders.
    
    The OrderItem model represents individual products within an order,
    capturing product details, quantities, pricing, and calculated totals.
    This design supports detailed order analysis, inventory tracking, and
    financial reconciliation at the line item level.
    
    🎯 Business Purpose:
        - Represent individual products within customer orders
        - Track quantities and pricing for each product
        - Enable detailed order analysis and reporting
        - Support inventory reservation and fulfillment workflows
        - Provide audit trail for pricing and quantity changes
    
    💰 Financial Calculations:
        - Unit pricing with decimal precision
        - Line total calculation (quantity × unit_price)
        - Price history preservation for audit purposes
        - Support for discounts and promotional pricing
        - Currency consistency with parent order
    
    📦 Inventory Integration:
        - Book ID reference for product catalog lookups
        - Quantity tracking for inventory reservation
        - Support for partial fulfillment scenarios
        - Integration with inventory availability checks
        - Backorder and substitution support
    
    📊 Data Structure:
        Identification:
        - id: UUID primary key for distributed system compatibility
        - order_id: Foreign key reference to parent Order
        - book_id: Reference to product in inventory system
        
        Quantity and Pricing:
        - quantity: Number of items ordered (integer)
        - unit_price: Price per item with decimal precision
        - line_total: Calculated total (quantity × unit_price)
        
        Relationships:
        - order: Many-to-one relationship with Order entity
    
    🛠️ Usage Examples:
        Creating order items:
        ```python
        order_item = OrderItem(
            order_id=order.id,
            book_id="book123",
            quantity=3,
            unit_price=Decimal("15.99"),
            line_total=Decimal("47.97")  # 3 × $15.99
        )
        ```
        
        Calculating order totals:
        ```python
        order_total = session.query(
            func.sum(OrderItem.line_total)
        ).filter_by(order_id=order_id).scalar()
        ```
        
        Inventory reservation:
        ```python
        # Reserve inventory for all items in order
        for item in order.items:
            inventory_service.reserve_item(
                book_id=item.book_id,
                quantity=item.quantity,
                order_id=order.id
            )
        ```
    
    🔒 Data Integrity:
        - Foreign key constraints maintain order relationship
        - Non-null constraints ensure data completeness
        - Decimal precision prevents financial calculation errors
        - Indexes on order_id and book_id for query performance
    
    📈 Query Performance:
        - order_id indexed for order item lookups
        - book_id indexed for product-based queries
        - Supports efficient aggregation queries
        - Optimized for order summary calculations
    
    🔗 Integration Points:
        - Inventory Service: Product details and availability
        - Pricing Service: Current pricing and discounts
        - Shipping Service: Item weight and dimensions
        - Analytics Service: Product performance metrics
    
    Version: 1.0.0
    Table: order_items
    """
    __tablename__ = "order_items"

    # Primary identification with UUID for distributed systems
    id = Column(String, primary_key=True, default=_uuid)
    
    # Foreign key relationship to parent order (indexed for performance)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)
    
    # Product reference (links to inventory service)
    book_id = Column(String, nullable=False, index=True)  # Indexed for product queries
    
    # Quantity and pricing with decimal precision
    quantity = Column(Integer, nullable=False)             # Number of items
    unit_price = Column(Numeric(10, 2), nullable=False)    # Price per item
    line_total = Column(Numeric(10, 2), nullable=False)    # Total for this line item

    # Many-to-one relationship with parent order
    order = relationship("Order", back_populates="items")

    def __repr__(self):
        """String representation for debugging and logging."""
        return f"<OrderItem(id={self.id}, book_id={self.book_id}, quantity={self.quantity}, total={self.line_total})>"


class IdempotencyKey(Base):
    """
    Idempotency key tracking for safe API operation retries.
    
    The IdempotencyKey model implements idempotency control to ensure that
    duplicate API requests (due to network issues, user double-clicks, etc.)
    do not result in duplicate orders or charges. This is critical for
    financial operations and user experience.
    
    🎯 Purpose:
        - Prevent duplicate order creation from retry attempts
        - Enable safe API operation retries without side effects
        - Provide consistent responses for duplicate requests
        - Support network reliability and fault tolerance
        - Ensure financial integrity in payment processing
    
    🔧 Idempotency Mechanism:
        - Client provides idempotency key with requests
        - Server stores key with request hash and result
        - Duplicate requests return cached result
        - Keys expire after configurable time period
        - Supports both automatic and manual key generation
    
    📊 Data Structure:
        Identification:
        - key: Client-provided or server-generated idempotency key
        - order_id: Result of the idempotent operation
        - request_hash: Hash of request parameters for validation
        - created_at: Timestamp for key expiration management
        
        Constraints:
        - Unique constraint on key field
        - Index on order_id for result lookups
    
    🛠️ Usage Examples:
        Storing idempotency key:
        ```python
        idempotency_key = IdempotencyKey(
            key="client-provided-key-123",
            order_id=order.id,
            request_hash=hashlib.sha256(
                json.dumps(request_data, sort_keys=True).encode()
            ).hexdigest(),
            created_at=datetime.utcnow()
        )
        ```
        
        Checking for duplicate requests:
        ```python
        existing_key = session.query(IdempotencyKey).filter_by(
            key=idempotency_key
        ).first()
        
        if existing_key:
            # Return existing result
            return existing_key.order_id
        else:
            # Process new request
            order = create_order(request_data)
            store_idempotency_key(idempotency_key, order.id)
        ```
        
        Key expiration cleanup:
        ```python
        # Remove expired keys (older than 24 hours)
        expiry_time = datetime.utcnow() - timedelta(hours=24)
        session.query(IdempotencyKey).filter(
            IdempotencyKey.created_at < expiry_time
        ).delete()
        ```
    
    🔒 Security Considerations:
        - Keys should be unpredictable to prevent abuse
        - Request hash prevents parameter manipulation
        - Regular cleanup prevents storage bloat
        - Rate limiting complements idempotency protection
    
    📈 Performance Characteristics:
        - Primary key lookup for O(1) duplicate detection
        - Indexed order_id for result retrieval
        - Periodic cleanup maintains table performance
        - Memory-efficient storage for high-volume operations
    
    🔗 Integration Points:
        - API Gateway: Idempotency key extraction and validation
        - Payment Service: Duplicate payment prevention
        - Order Service: Order creation and retrieval
        - Monitoring: Duplicate request metrics and alerting
    
    Version: 1.0.0
    Table: idempotency_keys
    """
    __tablename__ = "idempotency_keys"

    # Idempotency key as primary identifier
    key = Column(String, primary_key=True)
    
    # Result of the idempotent operation (indexed for lookups)
    order_id = Column(String, nullable=False, index=True)
    
    # Hash of request parameters for validation
    request_hash = Column(String, nullable=False)
    
    # Creation timestamp for expiration management
    created_at = Column(DateTime, default=datetime.utcnow)

    # Table constraints for data integrity
    __table_args__ = (
        UniqueConstraint("key"),  # Ensure key uniqueness
    )

    def __repr__(self):
        """String representation for debugging and logging."""
        return f"<IdempotencyKey(key={self.key}, order_id={self.order_id})>"


class OutboxEvent(Base):
    """
    Event storage for reliable message publishing using the outbox pattern.
    
    The OutboxEvent model implements the transactional outbox pattern to ensure
    reliable message publishing in distributed systems. Events are stored in
    the same transaction as business operations and processed asynchronously
    to guarantee at-least-once delivery semantics.
    
    🎯 Purpose:
        - Ensure reliable message publishing in distributed systems
        - Implement transactional outbox pattern for data consistency
        - Enable event-driven architecture with guaranteed delivery
        - Support eventual consistency across service boundaries
        - Provide audit trail for all published events
    
    🔄 Outbox Pattern Flow:
        1. Business operation and event storage in same transaction
        2. Background processor reads unprocessed events
        3. Events published to message broker (Kafka, RabbitMQ, etc.)
        4. Successful publication marked with processed_at timestamp
        5. Failed events retried with exponential backoff
        6. Processed events archived or cleaned up periodically
    
    📊 Event Types:
        Common event types in the checkout service:
        - OrderCreated: New order placed by customer
        - OrderUpdated: Order status or details changed
        - PaymentProcessed: Payment successfully completed
        - OrderCancelled: Order cancelled by customer or system
        - InventoryReserved: Items reserved for order
        - ShippingRequested: Order ready for fulfillment
    
    📊 Data Structure:
        Identification:
        - id: UUID primary key for event tracking
        - type: Event type for routing and processing
        
        Event Data:
        - payload: JSON event data with all necessary details
        - created_at: Event creation timestamp
        - processed_at: Event processing timestamp (null until processed)
    
    🛠️ Usage Examples:
        Storing events during order creation:
        ```python
        # Store business data and event in same transaction
        with session_scope() as db:
            # Create order
            order = Order(user_id="user123", total_amount=29.99)
            db.add(order)
            
            # Store event for publishing
            event = OutboxEvent(
                type="OrderCreated",
                payload={
                    "order_id": order.id,
                    "user_id": order.user_id,
                    "total_amount": str(order.total_amount),
                    "currency": order.currency,
                    "created_at": order.created_at.isoformat()
                }
            )
            db.add(event)
            # Both operations committed together
        ```
        
        Processing events for publication:
        ```python
        # Background processor reads unprocessed events
        unprocessed_events = session.query(OutboxEvent).filter(
            OutboxEvent.processed_at.is_(None)
        ).order_by(OutboxEvent.created_at).limit(100).all()
        
        for event in unprocessed_events:
            try:
                # Publish to message broker
                message_broker.publish(
                    topic=f"checkout.{event.type}",
                    message=event.payload
                )
                
                # Mark as processed
                event.processed_at = datetime.utcnow()
                session.commit()
                
            except Exception as e:
                # Handle publishing failures
                logger.error(f"Failed to publish event {event.id}: {e}")
                session.rollback()
        ```
        
        Event cleanup:
        ```python
        # Clean up old processed events (older than 30 days)
        cleanup_date = datetime.utcnow() - timedelta(days=30)
        session.query(OutboxEvent).filter(
            OutboxEvent.processed_at < cleanup_date
        ).delete()
        ```
    
    🔒 Reliability Guarantees:
        - At-least-once delivery semantics
        - Transactional consistency with business operations
        - Duplicate event handling via idempotency
        - Ordered processing within event types
        - Retry mechanisms for failed publications
    
    📈 Performance Considerations:
        - Indexes on processed_at for efficient querying
        - Batch processing for high-throughput scenarios
        - Periodic cleanup to maintain table performance
        - Event ordering preserved within transactions
    
    🔗 Integration Points:
        - Message Broker: Kafka, RabbitMQ, or similar
        - Event Processors: Background workers for event publishing
        - Monitoring: Event processing metrics and alerting
        - Analytics: Event streaming for real-time analytics
    
    Version: 1.0.0
    Table: outbox_events
    """
    __tablename__ = "outbox_events"

    # Primary identification with UUID for event tracking
    id = Column(String, primary_key=True, default=_uuid)
    
    # Event type for routing and processing logic
    type = Column(String, nullable=False, index=True)  # Indexed for type-based queries
    
    # Event data as JSON for flexible schema
    payload = Column(JSON, nullable=False)
    
    # Event lifecycle timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)  # Indexed for processing order
    processed_at = Column(DateTime, nullable=True, index=True)          # Indexed for status queries

    def __repr__(self):
        """String representation for debugging and logging."""
        status = "processed" if self.processed_at else "pending"
        return f"<OutboxEvent(id={self.id}, type={self.type}, status={status})>"


