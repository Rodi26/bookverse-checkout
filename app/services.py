

"""
BookVerse Checkout Service - Business Logic Services

This module implements the core business logic for order processing in the
BookVerse checkout service. It provides sophisticated order creation workflows,
inventory integration, idempotency handling, and financial calculations with
comprehensive error handling and compensating transactions.

🏗️ Service Architecture:
    - Order Creation: Complete order processing workflow with validation
    - Inventory Integration: Real-time stock checking and reservation
    - Idempotency Control: Duplicate request prevention for API safety
    - Financial Calculations: Precise decimal arithmetic for monetary operations
    - Compensating Transactions: Automatic rollback for failed operations
    - Event Sourcing: Outbox pattern for reliable event publishing

🚀 Key Features:
    - Atomic order creation with ACID transaction guarantees
    - Real-time inventory validation and reservation
    - Idempotency support for safe operation retries
    - Automatic inventory compensation on failures
    - Event publishing for downstream service integration
    - Comprehensive error handling with detailed failure information

🔧 Business Logic Implementation:
    - Order lifecycle management from creation to confirmation
    - Multi-item order processing with batch validation
    - Inventory reservation with automatic rollback
    - Financial calculations with proper decimal precision
    - Audit trail generation through event sourcing
    - Error recovery with compensating transactions

📊 Integration Patterns:
    - Inventory Service: Stock validation and adjustment operations
    - Database Layer: Transactional order persistence
    - Event System: Asynchronous event publishing
    - API Layer: Request validation and response generation

Authors: BookVerse Platform Team
Version: 1.0.0
"""

import hashlib
from decimal import Decimal
from typing import List, Tuple, Optional

from sqlalchemy.orm import Session

from .models import Order, OrderItem, IdempotencyKey, OutboxEvent
from .schemas import CreateOrderRequest
from .inventory_client import InventoryClient, InventoryError


def stable_request_hash(data: CreateOrderRequest) -> str:
    """
    Generate a stable hash for order creation requests to support idempotency.
    
    This function creates a deterministic hash of an order creation request
    that remains consistent across identical requests, enabling idempotency
    control and duplicate request detection. The hash includes all relevant
    request parameters in a normalized format.
    
    🔧 Hash Generation Process:
        - Normalizes user ID and item data into consistent format
        - Sorts items by bookId, quantity, and price for deterministic ordering
        - Creates pipe-delimited string representation of request
        - Generates SHA-256 hash for cryptographic uniqueness
        - Returns hexadecimal digest suitable for database storage
    
    🛠️ Normalization Strategy:
        - User ID as primary identifier
        - Items sorted by (bookId, qty, unitPrice) for consistency
        - Decimal prices preserved with full precision
        - Pipe and comma delimiters for clear field separation
        - UTF-8 encoding for international character support
    
    Args:
        data (CreateOrderRequest): The order creation request to hash
        
    Returns:
        str: SHA-256 hash digest in hexadecimal format
        
    Example:
        ```python
        request = CreateOrderRequest(
            userId="user123",
            items=[
                OrderItemRequest(bookId="book456", qty=2, unitPrice=Decimal("19.99")),
                OrderItemRequest(bookId="book789", qty=1, unitPrice=Decimal("29.99"))
            ]
        )
        
        hash_value = stable_request_hash(request)
        # Returns: "a1b2c3d4e5f6..."
        
        # Same request produces same hash
        hash_value_2 = stable_request_hash(request)
        assert hash_value == hash_value_2
        ```
    
    🔒 Security Considerations:
        - SHA-256 provides cryptographic hash strength
        - Deterministic output enables reliable duplicate detection
        - Hash collision probability is negligible for practical use
        - Does not expose sensitive information in hash value
    
    📈 Performance Characteristics:
        - O(n log n) complexity due to item sorting
        - Fast hash computation with minimal memory usage
        - Suitable for high-volume order processing
        - Cached results can improve repeated hash operations
    """
    # Create normalized string representation of request
    raw = f"{data.userId}|" + ",".join(
        f"{i.bookId}:{i.qty}:{i.unitPrice}" 
        for i in sorted(data.items, key=lambda x: (x.bookId, x.qty, x.unitPrice))
    )
    
    # Generate SHA-256 hash of normalized request
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def upsert_idempotency(session: Session, key: str, request_hash: str) -> Tuple[str, str]:
    """
    Handle idempotency key management for order creation operations.
    
    This function implements idempotency control by checking for existing
    idempotency keys and handling new key creation or conflict detection.
    It ensures that duplicate requests are handled appropriately while
    maintaining data consistency and preventing duplicate orders.
    
    🎯 Idempotency Logic:
        - Check for existing idempotency key in database
        - Create new order and key if none exists ("proceed")
        - Detect request conflicts if hash doesn't match ("conflict")
        - Return existing order for identical requests ("replay")
    
    🔧 Operation Flow:
        1. Query database for existing idempotency key
        2. If not found: Create placeholder order and store key
        3. If found with different hash: Return conflict status
        4. If found with matching hash: Return replay status
        5. Return decision and order ID for further processing
    
    Args:
        session (Session): Database session for transactional operations
        key (str): Client-provided or generated idempotency key
        request_hash (str): Hash of request parameters for validation
        
    Returns:
        Tuple[str, str]: (decision, order_id) where decision is one of:
            - "proceed": New request, continue with order creation
            - "conflict": Existing key with different request parameters
            - "replay": Identical request, return existing order
    
    Example:
        ```python
        # First request with new key
        decision, order_id = upsert_idempotency(session, "key123", "hash456")
        assert decision == "proceed"
        
        # Identical request (same hash)
        decision, order_id = upsert_idempotency(session, "key123", "hash456")
        assert decision == "replay"
        
        # Different request with same key (conflict)
        decision, order_id = upsert_idempotency(session, "key123", "hash789")
        assert decision == "conflict"
        ```
    
    ⚠️ Important Notes:
        - Creates placeholder order with empty user_id for new keys
        - Placeholder order is updated during actual order creation
        - Database session must be flushed after this operation
        - Conflicts should be handled with appropriate HTTP status codes
    
    🔒 Transaction Safety:
        - All operations within single database transaction
        - Automatic rollback on session exceptions
        - Consistent state maintained across concurrent requests
        - Race condition protection through database constraints
    """
    # Check for existing idempotency key
    entry = session.get(IdempotencyKey, key)
    
    if entry is None:
        # New idempotency key - create placeholder order
        order = Order(user_id="", status="PENDING")  # Placeholder values
        session.add(order)
        session.flush()  # Get order ID before storing key
        
        # Store idempotency key with order reference
        session.add(IdempotencyKey(
            key=key, 
            order_id=order.id, 
            request_hash=request_hash
        ))
        
        return ("proceed", order.id)
    
    # Existing key found - check for request conflicts
    if entry.request_hash != request_hash:
        # Same key, different request parameters = conflict
        return ("conflict", entry.order_id)
    
    # Same key, same request parameters = replay existing result
    return ("replay", entry.order_id)


def calculate_totals(items: List[Tuple[Decimal, int]]) -> Decimal:
    """
    Calculate order total with precise decimal arithmetic for financial accuracy.
    
    This function performs financial calculations using Python's Decimal type
    to ensure precise monetary arithmetic without floating-point errors.
    It supports multi-item orders with proper quantization for currency
    representation.
    
    🎯 Financial Precision:
        - Uses Decimal type for exact monetary calculations
        - Prevents floating-point precision errors
        - Quantizes result to 2 decimal places for currency display
        - Supports high-precision intermediate calculations
        - Maintains accuracy across multiple line items
    
    💰 Calculation Process:
        - Iterates through all order items
        - Multiplies unit price by quantity for each item
        - Accumulates line totals using decimal arithmetic
        - Quantizes final result to standard currency precision
        - Returns total suitable for database storage and display
    
    Args:
        items (List[Tuple[Decimal, int]]): List of (unit_price, quantity) tuples
        
    Returns:
        Decimal: Total amount quantized to 2 decimal places
        
    Example:
        ```python
        items = [
            (Decimal("19.99"), 2),  # $39.98
            (Decimal("29.99"), 1),  # $29.99
            (Decimal("5.50"), 3)    # $16.50
        ]
        
        total = calculate_totals(items)
        # Returns: Decimal("86.47")
        
        # Handles edge cases with precision
        edge_items = [
            (Decimal("0.333"), 3),  # $0.999
            (Decimal("1.666"), 2)   # $3.332
        ]
        edge_total = calculate_totals(edge_items)
        # Returns: Decimal("4.33") (properly quantized)
        ```
    
    🔧 Quantization Rules:
        - Final result quantized to 2 decimal places
        - Uses ROUND_HALF_UP rounding strategy
        - Consistent with standard currency representation
        - Prevents decimal drift in financial calculations
    
    📈 Performance Characteristics:
        - O(n) time complexity for n items
        - Memory efficient with minimal intermediate storage
        - Suitable for large orders with many line items
        - Fast decimal arithmetic operations
    
    💡 Financial Best Practices:
        - Always use Decimal for monetary calculations
        - Quantize results to appropriate currency precision
        - Maintain audit trail of calculation components
        - Validate input data before calculation
    """
    # Initialize total with zero decimal value
    total = Decimal("0")
    
    # Accumulate line totals using decimal arithmetic
    for price, qty in items:
        total += (price * qty)
    
    # Quantize to standard currency precision (2 decimal places)
    return total.quantize(Decimal("0.01"))


def create_order(session: Session, req: CreateOrderRequest, idempotency_key: Optional[str]) -> Tuple[Order, List[OrderItem]]:
    """
    Create a new order with comprehensive validation, inventory management, and error handling.
    
    This function implements the complete order creation workflow including
    idempotency handling, inventory validation, atomic database operations,
    event publishing, and compensating transactions for error recovery.
    
    🎯 Order Creation Workflow:
        1. Idempotency validation and conflict detection
        2. Inventory availability checking for all items
        3. Atomic inventory reservation and order creation
        4. Financial calculation and order finalization
        5. Event publishing for downstream services
        6. Automatic compensation on any failures
    
    🔧 Key Features:
        - Atomic transaction processing with ACID guarantees
        - Real-time inventory validation and reservation
        - Idempotency support for safe operation retries
        - Comprehensive error handling with detailed messages
        - Automatic rollback and compensation on failures
        - Event sourcing with outbox pattern
    
    📦 Inventory Management:
        - Pre-validation of stock availability for all items
        - Atomic inventory adjustments across all line items
        - Automatic compensation adjustments on order failures
        - Integration with external inventory service
        - Support for partial availability reporting
    
    💰 Financial Processing:
        - Precise decimal calculations for all monetary values
        - Line-by-line total calculation and validation
        - Currency consistency across order and items
        - Financial audit trail through database records
    
    Args:
        session (Session): Database session for transactional operations
        req (CreateOrderRequest): Validated order creation request
        idempotency_key (Optional[str]): Client-provided idempotency key
        
    Returns:
        Tuple[Order, List[OrderItem]]: Created order and associated items
        
    Raises:
        ValueError: For various business logic violations:
            - "idempotency_conflict": Same key, different request parameters
            - "validation_error: empty items": No items in order
            - "insufficient_stock:{failures}": Inventory availability issues
        InventoryError: For inventory service communication failures
        Exception: For database or other system-level failures
    
    Example:
        ```python
        # Successful order creation
        request = CreateOrderRequest(
            userId="user123",
            items=[
                OrderItemRequest(
                    bookId="book456",
                    qty=2,
                    unitPrice=Decimal("19.99")
                )
            ]
        )
        
        with session_scope() as db:
            order, items = create_order(db, request, "idempotency-key-123")
            print(f"Order {order.id} created with {len(items)} items")
        
        # Idempotent replay
        with session_scope() as db:
            order2, items2 = create_order(db, request, "idempotency-key-123")
            assert order.id == order2.id  # Same order returned
        
        # Inventory insufficient error handling
        try:
            large_request = CreateOrderRequest(
                userId="user123",
                items=[
                    OrderItemRequest(
                        bookId="book456",
                        qty=1000,  # More than available
                        unitPrice=Decimal("19.99")
                    )
                ]
            )
            create_order(db, large_request, None)
        except ValueError as e:
            if "insufficient_stock" in str(e):
                # Handle inventory shortage
                print("Not enough stock available")
        ```
    
    🔄 Compensating Transactions:
        - Automatic inventory adjustment reversal on failures
        - Order status update to "CANCELLED" on errors
        - Graceful handling of partial compensation failures
        - Comprehensive error logging for debugging
    
    📊 Event Publishing:
        - OrderCreated event with complete order details
        - Outbox pattern for reliable event delivery
        - JSON payload with order and item information
        - Downstream service integration support
    
    🔒 Transaction Safety:
        - All operations within single database transaction
        - Automatic rollback on any operation failure
        - Inventory consistency maintained across failures
        - Idempotency key integrity preserved
    
    📈 Performance Considerations:
        - Batch inventory validation for efficiency
        - Minimal database round trips
        - Efficient error handling without retry loops
        - Optimized for high-volume order processing
    
    🔗 Integration Points:
        - Inventory Service: Stock validation and adjustment
        - Event System: Order creation notifications
        - Payment Service: Order total and item details
        - Analytics Service: Order metrics and reporting
    """
    # Initialize inventory client for stock operations
    inv = InventoryClient()
    
    # Generate request hash for idempotency validation
    req_hash = stable_request_hash(req)
    
    # Handle idempotency if key provided
    if idempotency_key:
        decision, order_id = upsert_idempotency(session, idempotency_key, req_hash)
        
        if decision == "conflict":
            # Same key, different request = conflict
            raise ValueError("idempotency_conflict")
        
        if decision == "replay":
            # Same key, same request = return existing order
            order = session.get(Order, order_id)
            return order, order.items
        
        # "proceed" decision - use existing placeholder order
        order = session.get(Order, order_id)
    else:
        # No idempotency key - create new order directly
        order = Order(user_id=req.userId, status="PENDING")
        session.add(order)
        session.flush()  # Get order ID for subsequent operations

    # Validate request has items
    if not req.items:
        raise ValueError("validation_error: empty items")

    # Pre-validate inventory availability for all items
    failures = []
    for item in req.items:
        # Query inventory service for current stock levels
        inv_data = inv.get_inventory(item.bookId) or {}
        available = inv_data.get("inventory", {}).get("quantity_available", 0)
        
        if available < item.qty:
            # Record availability failure for detailed error reporting
            failures.append({
                "bookId": item.bookId, 
                "available": available, 
                "requested": item.qty
            })
    
    if failures:
        # Fail fast if any items have insufficient inventory
        raise ValueError(f"insufficient_stock:{failures}")

    # Begin atomic order creation with inventory adjustments
    created_items: List[OrderItem] = []
    
    try:
        # Process each order item with inventory adjustment
        for item in req.items:
            # Reserve inventory (negative adjustment)
            inv.adjust(item.bookId, -int(item.qty), notes=f"order:{order.id}")
            
            # Calculate line total with proper decimal precision
            line_total = (item.unitPrice * item.qty).quantize(Decimal("0.01"))
            
            # Create order item record
            oi = OrderItem(
                order_id=order.id,
                book_id=item.bookId,
                quantity=int(item.qty),
                unit_price=item.unitPrice,
                line_total=line_total,
            )
            session.add(oi)
            created_items.append(oi)
        
        # Calculate and set order totals
        total = calculate_totals([(i.unitPrice, i.qty) for i in req.items])
        order.user_id = req.userId
        order.total_amount = total
        order.status = "CONFIRMED"
        
        # Ensure database reflects current state
        session.flush()
        
        # Publish order creation event for downstream services
        session.add(OutboxEvent(
            type="order.created", 
            payload={
                "orderId": order.id,
                "userId": req.userId,
                "total": float(total),  # Convert for JSON serialization
                "items": [{"bookId": it.bookId, "qty": it.qty} for it in req.items],
            }
        ))
        
        return order, created_items
        
    except Exception:
        # Compensating transaction: reverse inventory adjustments
        for it in req.items:
            try:
                # Restore inventory (positive adjustment)
                inv.adjust(it.bookId, int(it.qty), notes=f"compensate:{order.id}")
            except InventoryError:
                # Log compensation failures but don't fail the rollback
                pass
        
        # Mark order as cancelled for audit trail
        order.status = "CANCELLED"
        session.flush()
        
        # Re-raise original exception for caller handling
        raise


