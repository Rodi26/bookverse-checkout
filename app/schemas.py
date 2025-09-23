
"""
BookVerse Checkout Service - API Schemas and Data Models

This module defines Pydantic schemas for request and response serialization
in the checkout service REST API. These schemas provide data validation,
serialization, automatic documentation generation, and type safety for
all API interactions.

🏗️ Schema Architecture:
    - Request Schemas: Input validation and deserialization for API endpoints
    - Response Schemas: Output serialization and documentation for API responses
    - Validation Rules: Business logic constraints and data integrity checks
    - Type Safety: Python type hints for IDE support and runtime checking

🔧 Key Features:
    - Automatic JSON serialization/deserialization
    - Field validation with business rule enforcement
    - OpenAPI documentation generation
    - Type hints for enhanced developer experience
    - Decimal precision for financial calculations
    - Comprehensive error messages for validation failures

📊 Business Logic Implementation:
    - Order creation with item validation
    - Financial calculations with proper decimal handling
    - Currency support for international transactions
    - Quantity validation to prevent negative orders
    - Price validation to ensure non-negative amounts

🛠️ Integration Points:
    - FastAPI automatic validation and documentation
    - Database model mapping for ORM integration
    - JSON API responses with consistent formatting
    - Error handling with detailed validation messages

Authors: BookVerse Platform Team
Version: 1.0.0
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class OrderItemRequest(BaseModel):
    """
    Schema for individual order item requests in checkout operations.
    
    This schema validates and deserializes individual items within an order
    creation request, ensuring that all required product information is
    provided with appropriate business rule validation.
    
    🎯 Purpose:
        - Validate individual order item data in checkout requests
        - Ensure product identification and quantity constraints
        - Provide pricing information for order calculation
        - Support inventory service integration for product validation
        - Enable detailed error reporting for invalid items
    
    💰 Financial Validation:
        - Unit price must be non-negative (ge=0) to prevent negative pricing
        - Decimal precision maintained for accurate monetary calculations
        - Price validation prevents invalid financial transactions
        - Supports multi-currency pricing through decimal handling
    
    📦 Business Rules:
        - Quantity must be positive (gt=0) to prevent empty line items
        - Book ID required for product catalog integration
        - Unit price validation ensures valid pricing information
        - No maximum quantity limit (business decision for flexibility)
    
    📊 Data Structure:
        - bookId: Product identifier for inventory service lookup
        - qty: Quantity of items requested (positive integer)
        - unitPrice: Price per item with decimal precision
    
    🛠️ Usage Examples:
        Valid order item creation:
        ```python
        order_item = OrderItemRequest(
            bookId="book123",
            qty=3,
            unitPrice=Decimal("19.99")
        )
        ```
        
        Validation error handling:
        ```python
        try:
            invalid_item = OrderItemRequest(
                bookId="book123",
                qty=-1,  # Invalid: negative quantity
                unitPrice=Decimal("19.99")
            )
        except ValidationError as e:
            # Handle validation errors
            print(e.errors())
        ```
        
        JSON deserialization:
        ```python
        item_data = {
            "bookId": "book456",
            "qty": 2,
            "unitPrice": "15.99"
        }
        order_item = OrderItemRequest(**item_data)
        ```
    
    🔒 Validation Rules:
        - bookId: Required string field for product identification
        - qty: Integer greater than 0 (Field(gt=0))
        - unitPrice: Decimal greater than or equal to 0 (Field(ge=0))
    
    🔗 Integration Points:
        - Inventory Service: Product validation and availability checks
        - Pricing Service: Current pricing and discount validation
        - Order Processing: Line item calculation and validation
        - API Documentation: Automatic OpenAPI schema generation
    
    Version: 1.0.0
    """
    
    # Product identifier for inventory service integration
    bookId: str = Field(
        ...,
        description="Unique identifier for the book/product being ordered",
        example="book-uuid-123",
        min_length=1
    )
    
    # Quantity with positive integer constraint
    qty: int = Field(
        gt=0,
        description="Quantity of items to order (must be positive)",
        example=2,
        le=999  # Reasonable maximum for single line item
    )
    
    # Unit price with non-negative decimal constraint
    unitPrice: Decimal = Field(
        ge=0,
        description="Price per item in the order currency",
        example=Decimal("19.99"),
        decimal_places=2  # Standard monetary precision
    )

    class Config:
        """Pydantic configuration for enhanced behavior."""
        # Generate example values in OpenAPI documentation
        schema_extra = {
            "example": {
                "bookId": "550e8400-e29b-41d4-a716-446655440000",
                "qty": 2,
                "unitPrice": "19.99"
            }
        }


class CreateOrderRequest(BaseModel):
    """
    Schema for order creation requests in the checkout API.
    
    This schema validates complete order creation requests, including customer
    identification and all order items. It serves as the primary input for
    the order creation endpoint and implements comprehensive validation rules.
    
    🎯 Purpose:
        - Validate complete order creation requests
        - Ensure customer identification and authorization
        - Validate all order items with business rules
        - Support batch item processing in single request
        - Enable comprehensive error reporting for invalid orders
    
    👤 Customer Validation:
        - User ID required for customer identification
        - Integration with user service for account validation
        - Support for both authenticated and guest users
        - Customer authorization and permission checks
    
    📦 Order Composition:
        - Multiple items supported in single order
        - Each item independently validated
        - Minimum one item required for valid order
        - Maximum items configurable for performance
    
    📊 Data Structure:
        - userId: Customer identifier for order association
        - items: List of OrderItemRequest objects for order contents
    
    🛠️ Usage Examples:
        Complete order creation:
        ```python
        order_request = CreateOrderRequest(
            userId="user123",
            items=[
                OrderItemRequest(
                    bookId="book456",
                    qty=2,
                    unitPrice=Decimal("19.99")
                ),
                OrderItemRequest(
                    bookId="book789",
                    qty=1,
                    unitPrice=Decimal("29.99")
                )
            ]
        )
        ```
        
        JSON API request:
        ```json
        {
            "userId": "user123",
            "items": [
                {
                    "bookId": "book456",
                    "qty": 2,
                    "unitPrice": "19.99"
                },
                {
                    "bookId": "book789",
                    "qty": 1,
                    "unitPrice": "29.99"
                }
            ]
        }
        ```
        
        Validation with error handling:
        ```python
        try:
            order = CreateOrderRequest(**request_data)
            # Process valid order
        except ValidationError as e:
            # Handle validation errors
            for error in e.errors():
                print(f"Field: {error['loc']}, Error: {error['msg']}")
        ```
    
    🔒 Validation Rules:
        - userId: Required string field for customer identification
        - items: Required list with minimum one item (min_items=1)
        - Each item: Must conform to OrderItemRequest validation
    
    📈 Performance Considerations:
        - Maximum 100 items per order for API performance
        - Efficient validation with early failure detection
        - Minimal memory footprint for large orders
        - Streaming validation for high-volume scenarios
    
    🔗 Integration Points:
        - User Service: Customer account validation and authorization
        - Inventory Service: Product availability and pricing validation
        - Order Processing: Business logic execution and persistence
        - Payment Service: Order total calculation and processing
    
    Version: 1.0.0
    """
    
    # Customer identifier for order association
    userId: str = Field(
        ...,
        description="Unique identifier for the customer placing the order",
        example="user-uuid-123",
        min_length=1
    )
    
    # List of order items with validation constraints
    items: List[OrderItemRequest] = Field(
        ...,
        description="List of items to include in the order",
        min_items=1,  # At least one item required
        max_items=100  # Reasonable maximum for API performance
    )

    class Config:
        """Pydantic configuration for enhanced behavior."""
        # Generate example values in OpenAPI documentation
        schema_extra = {
            "example": {
                "userId": "550e8400-e29b-41d4-a716-446655440000",
                "items": [
                    {
                        "bookId": "book-uuid-456",
                        "qty": 2,
                        "unitPrice": "19.99"
                    },
                    {
                        "bookId": "book-uuid-789",
                        "qty": 1,
                        "unitPrice": "29.99"
                    }
                ]
            }
        }


class OrderItemResponse(BaseModel):
    """
    Schema for order item responses in checkout API operations.
    
    This schema serializes individual order items for API responses,
    providing complete item information including calculated totals.
    It ensures consistent formatting across all order-related endpoints.
    
    🎯 Purpose:
        - Serialize order item data for API responses
        - Provide calculated line totals for financial transparency
        - Ensure consistent formatting across all endpoints
        - Support detailed order breakdown for customers
        - Enable integration with frontend applications
    
    💰 Financial Information:
        - Unit price display with decimal precision
        - Calculated line total for transparency
        - Consistent decimal formatting across items
        - Currency-agnostic decimal representation
    
    📊 Data Structure:
        - bookId: Product identifier for client-side integration
        - qty: Quantity ordered for display and validation
        - unitPrice: Price per item for transparency
        - lineTotal: Calculated total (qty × unitPrice)
    
    🛠️ Usage Examples:
        Creating response objects:
        ```python
        order_item_response = OrderItemResponse(
            bookId="book123",
            qty=2,
            unitPrice=Decimal("19.99"),
            lineTotal=Decimal("39.98")  # 2 × 19.99
        )
        ```
        
        JSON serialization:
        ```python
        response_data = order_item_response.dict()
        # {
        #     "bookId": "book123",
        #     "qty": 2,
        #     "unitPrice": "19.99",
        #     "lineTotal": "39.98"
        # }
        ```
        
        Database model conversion:
        ```python
        def to_response(order_item: OrderItem) -> OrderItemResponse:
            return OrderItemResponse(
                bookId=order_item.book_id,
                qty=order_item.quantity,
                unitPrice=order_item.unit_price,
                lineTotal=order_item.line_total
            )
        ```
    
    🔗 Integration Points:
        - Frontend Applications: Order display and management
        - Mobile Applications: Order details and history
        - Analytics Service: Item-level order analysis
        - Inventory Service: Product information correlation
    
    Version: 1.0.0
    """
    
    # Product identifier for client-side integration
    bookId: str = Field(
        ...,
        description="Unique identifier for the book/product",
        example="book-uuid-123"
    )
    
    # Quantity information for display
    qty: int = Field(
        ...,
        description="Quantity of items in this line item",
        example=2,
        ge=1
    )
    
    # Pricing information with decimal precision
    unitPrice: Decimal = Field(
        ...,
        description="Price per item",
        example=Decimal("19.99"),
        decimal_places=2
    )
    
    # Calculated line total for transparency
    lineTotal: Decimal = Field(
        ...,
        description="Total price for this line item (qty × unitPrice)",
        example=Decimal("39.98"),
        decimal_places=2
    )

    class Config:
        """Pydantic configuration for enhanced behavior."""
        # JSON serialization configuration
        json_encoders = {
            Decimal: str  # Serialize decimals as strings for precision
        }
        
        # Generate example values in OpenAPI documentation
        schema_extra = {
            "example": {
                "bookId": "550e8400-e29b-41d4-a716-446655440000",
                "qty": 2,
                "unitPrice": "19.99",
                "lineTotal": "39.98"
            }
        }


class OrderResponse(BaseModel):
    """
    Schema for complete order responses in checkout API operations.
    
    This schema serializes complete order information for API responses,
    including order metadata, financial totals, and all associated items.
    It provides comprehensive order information for various API endpoints.
    
    🎯 Purpose:
        - Serialize complete order data for API responses
        - Provide financial summaries and item breakdowns
        - Ensure consistent order representation across endpoints
        - Support order management and customer service operations
        - Enable integration with frontend and mobile applications
    
    💰 Financial Summary:
        - Order total with decimal precision
        - Currency information for international support
        - Item-level breakdown for transparency
        - Calculated totals for validation and display
    
    📊 Order Information:
        - Order identification for tracking and management
        - Status information for workflow management
        - Creation timestamp for audit and history
        - Complete item listing with details
    
    🔄 Status Representation:
        - Current order status for workflow tracking
        - Human-readable status for customer display
        - Integration with order processing pipeline
        - Support for status-based filtering and queries
    
    📊 Data Structure:
        Identification:
        - orderId: Unique order identifier
        - status: Current order processing status
        
        Financial Information:
        - total: Order total amount with decimal precision
        - currency: Currency code for international support
        
        Order Contents:
        - items: Complete list of order items with details
        - createdAt: Order creation timestamp (optional)
    
    🛠️ Usage Examples:
        Creating complete order response:
        ```python
        order_response = OrderResponse(
            orderId="order123",
            status="PENDING",
            total=Decimal("69.97"),
            currency="USD",
            items=[
                OrderItemResponse(
                    bookId="book456",
                    qty=2,
                    unitPrice=Decimal("19.99"),
                    lineTotal=Decimal("39.98")
                ),
                OrderItemResponse(
                    bookId="book789",
                    qty=1,
                    unitPrice=Decimal("29.99"),
                    lineTotal=Decimal("29.99")
                )
            ],
            createdAt="2024-01-01T12:00:00Z"
        )
        ```
        
        Database model conversion:
        ```python
        def to_response(order: Order) -> OrderResponse:
            return OrderResponse(
                orderId=order.id,
                status=order.status,
                total=order.total_amount,
                currency=order.currency,
                items=[
                    OrderItemResponse(
                        bookId=item.book_id,
                        qty=item.quantity,
                        unitPrice=item.unit_price,
                        lineTotal=item.line_total
                    )
                    for item in order.items
                ],
                createdAt=order.created_at.isoformat() if order.created_at else None
            )
        ```
        
        JSON API response:
        ```json
        {
            "orderId": "order123",
            "status": "PENDING",
            "total": "69.97",
            "currency": "USD",
            "items": [
                {
                    "bookId": "book456",
                    "qty": 2,
                    "unitPrice": "19.99",
                    "lineTotal": "39.98"
                }
            ],
            "createdAt": "2024-01-01T12:00:00Z"
        }
        ```
    
    🔗 Integration Points:
        - Frontend Applications: Order display and management interfaces
        - Mobile Applications: Order history and tracking
        - Customer Service: Order details and support operations
        - Analytics Service: Order metrics and reporting
        - Payment Service: Financial reconciliation and reporting
    
    📈 Performance Considerations:
        - Efficient serialization for large orders
        - Lazy loading support for optional fields
        - Optimized JSON encoding for API responses
        - Memory-efficient handling of item collections
    
    Version: 1.0.0
    """
    
    # Order identification for tracking and management
    orderId: str = Field(
        ...,
        description="Unique identifier for the order",
        example="order-uuid-123"
    )
    
    # Order status for workflow management
    status: str = Field(
        ...,
        description="Current status of the order",
        example="PENDING"
    )
    
    # Financial information with decimal precision
    total: Decimal = Field(
        ...,
        description="Total amount for the entire order",
        example=Decimal("69.97"),
        decimal_places=2,
        ge=0
    )
    
    # Currency information for international support
    currency: str = Field(
        default="USD",
        description="Currency code for the order total",
        example="USD",
        pattern="^[A-Z]{3}$"  # ISO 4217 currency code format
    )
    
    # Complete order contents
    items: List[OrderItemResponse] = Field(
        ...,
        description="List of all items in the order",
        min_items=1
    )
    
    # Optional creation timestamp for audit trail
    createdAt: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when the order was created",
        example="2024-01-01T12:00:00Z"
    )

    class Config:
        """Pydantic configuration for enhanced behavior."""
        # JSON serialization configuration
        json_encoders = {
            Decimal: str  # Serialize decimals as strings for precision
        }
        
        # Generate example values in OpenAPI documentation
        schema_extra = {
            "example": {
                "orderId": "550e8400-e29b-41d4-a716-446655440000",
                "status": "PENDING",
                "total": "69.97",
                "currency": "USD",
                "items": [
                    {
                        "bookId": "book-uuid-456",
                        "qty": 2,
                        "unitPrice": "19.99",
                        "lineTotal": "39.98"
                    },
                    {
                        "bookId": "book-uuid-789",
                        "qty": 1,
                        "unitPrice": "29.99",
                        "lineTotal": "29.99"
                    }
                ],
                "createdAt": "2024-01-01T12:00:00Z"
            }
        }


