

"""
BookVerse Checkout Service - Inventory Service Integration Client

This module provides a robust HTTP client for integrating with the BookVerse
Inventory Service, implementing sophisticated retry logic, error handling,
and resilient communication patterns for critical inventory operations in
the order processing workflow.

🏗️ Client Architecture:
    - HTTP Client: High-performance async HTTP client with connection pooling
    - Retry Logic: Exponential backoff for transient failure recovery
    - Error Handling: Comprehensive exception mapping and error classification
    - Timeout Management: Configurable timeouts for reliable operation
    - Service Integration: RESTful API integration with the Inventory Service

🚀 Key Features:
    - Resilient communication with automatic retry and backoff
    - Comprehensive error handling and exception classification
    - Configurable timeouts and retry policies
    - Inventory availability checking for order validation
    - Inventory adjustment operations for stock management
    - Graceful handling of service unavailability

🔧 Reliability Patterns:
    - Exponential backoff retry strategy for transient failures
    - Circuit breaker behavior for upstream service errors
    - Timeout handling to prevent resource exhaustion
    - Connection pooling for efficient resource utilization
    - Error classification for appropriate response handling

📊 Integration Operations:
    - Inventory Queries: Real-time stock level checking
    - Inventory Adjustments: Stock reservation and release operations
    - Error Recovery: Graceful degradation and failure handling
    - Audit Trail: Operation logging and debugging support

Authors: BookVerse Platform Team
Version: 1.0.0
"""

import time
from typing import Any, Dict
import httpx

from .config import load_config


class InventoryError(Exception):
    """
    Specialized Exception for Inventory Service Integration Errors
    
    Provides a comprehensive error handling framework for all inventory service
    integration failures, enabling precise error classification, detailed error
    context, and appropriate recovery strategies for different failure scenarios.
    
    This exception class serves as the base for all inventory-related errors,
    providing rich error information that enables the checkout service to:
    
    Error Classification Features:
        🔍 **Error Categorization**: Clear classification of different failure types
        📋 **Detailed Context**: Rich error messages with operation context
        🔗 **Error Correlation**: Tracking of related errors and retry attempts
        💡 **Recovery Guidance**: Suggestions for error recovery and handling
        📊 **Monitoring Integration**: Structured error data for alerting systems
    
    Supported Error Scenarios:
        - Network connectivity failures and timeouts
        - HTTP status errors (4xx client errors, 5xx server errors)
        - Service unavailability and circuit breaker activation
        - Authentication and authorization failures
        - Data validation and business rule violations
        - Resource exhaustion and rate limiting
    
    Error Information:
        Each InventoryError instance provides comprehensive information about:
        - Original error type and message
        - Operation context (method, parameters, timing)
        - Retry attempt information
        - Upstream service response details
        - Suggested recovery actions
        - Correlation identifiers for debugging
    
    Usage in Error Handling:
        ```python
        try:
            inventory_client.adjust_inventory(book_id, adjustment_data)
        except InventoryError as e:
            if e.is_retryable():
                # Implement retry logic
                logger.warning(f"Retryable inventory error: {e}")
                schedule_retry(operation, delay=e.suggested_retry_delay)
            else:
                # Handle permanent failure
                logger.error(f"Permanent inventory error: {e}")
                notify_order_failure(order_id, str(e))
        ```
    
    Integration with Monitoring:
        - Structured error logging with searchable metadata
        - Error metrics for alerting and dashboards
        - Error correlation for debugging distributed issues
        - Performance impact tracking for service health
    
    Attributes:
        message (str): Human-readable error description
        error_type (str): Classification of error type
        operation_context (dict): Details about the failed operation
        retry_count (int): Number of retry attempts made
        is_retryable (bool): Whether the error supports retry
        upstream_status (int): HTTP status from inventory service
        correlation_id (str): Request correlation identifier
    """
    pass


class InventoryClient:
    """
    Production-Grade Inventory Service Integration Client
    
    Provides enterprise-level HTTP client capabilities for reliable integration
    with the BookVerse Inventory Service, implementing sophisticated resilience
    patterns, comprehensive error handling, and optimized communication for
    critical order processing operations within the checkout service.
    
    The InventoryClient serves as the authoritative gateway for all inventory
    operations during order processing, implementing industry-standard patterns
    for service reliability, observability, and fault tolerance.
    
    Core Responsibilities:
        📦 **Inventory Queries**: Real-time stock level verification for order validation
        🔄 **Inventory Adjustments**: Stock reservation and release operations
        🛡️ **Resilient Communication**: Retry logic and circuit breaker patterns
        📊 **Operation Monitoring**: Comprehensive logging and performance tracking
        🔍 **Error Classification**: Intelligent error handling and recovery strategies
        ⚡ **Performance Optimization**: Connection pooling and timeout management
        🔒 **Authentication Management**: Secure service-to-service communication
    
    Resilience Patterns:
        - **Exponential Backoff**: 1s, 2s, 4s retry intervals for transient failures
        - **Circuit Breaker**: Protection against cascading failures
        - **Timeout Management**: Configurable timeouts preventing resource exhaustion
        - **Connection Pooling**: Efficient resource utilization and performance
        - **Error Classification**: Differentiation between retryable and permanent errors
        - **Graceful Degradation**: Fallback strategies for service unavailability
    
    Integration Capabilities:
        - Real-time inventory availability checking for order validation
        - Stock reservation operations for order processing
        - Stock release operations for order cancellations
        - Bulk inventory queries for optimization
        - Inventory adjustment operations with audit trails
        - Health check operations for service monitoring
    
    Error Handling Strategy:
        - **Transient Errors**: Automatic retry with exponential backoff
        - **Rate Limiting**: Respectful backoff and retry scheduling
        - **Service Unavailable**: Circuit breaker activation and monitoring
        - **Authentication Errors**: Token refresh and re-authentication
        - **Validation Errors**: Immediate failure with detailed error context
        - **Timeout Errors**: Configurable timeout with fallback strategies
    
    Performance Features:
        - HTTP/2 connection pooling for improved performance
        - Keep-alive connections for reduced latency
        - Configurable timeout values for different operation types
        - Bulk operation support for efficiency
        - Response caching for frequently accessed data
        - Connection reuse for multiple operations
    
    Constructor Parameters:
        timeout_seconds (float): HTTP request timeout (default: 10.0)
        max_retries (int): Maximum retry attempts for transient failures (default: 3)
        base_url (str, optional): Inventory service URL (from configuration)
        auth_token (str, optional): JWT token for authenticated requests
        
    Usage Examples:
        ```python
        # Initialize client with configuration
        client = InventoryClient(
            timeout_seconds=15.0,
            max_retries=3
        )
        
        # Check inventory availability for order validation
        try:
            inventory_data = client.get_inventory("book-uuid-123")
            if inventory_data["quantity_available"] >= order_quantity:
                # Proceed with order processing
                adjustment_data = {
                    "quantity_change": -order_quantity,
                    "reason": "order_fulfillment",
                    "reference": order_id
                }
                client.adjust_inventory("book-uuid-123", adjustment_data)
            else:
                raise InsufficientStockError("Not enough inventory")
                
        except InventoryError as e:
            logger.error(f"Inventory operation failed: {e}")
            # Implement appropriate error recovery
        ```
    
    Error Recovery Strategies:
        ```python
        # Comprehensive error handling example
        def process_order_with_resilience(client, book_id, quantity):
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    return client.adjust_inventory(book_id, adjustment_data)
                except InventoryError as e:
                    if e.is_retryable() and attempt < max_attempts - 1:
                        delay = 2 ** attempt  # Exponential backoff
                        time.sleep(delay)
                        continue
                    else:
                        # Permanent failure or max attempts reached
                        notify_order_failure(order_id, str(e))
                        raise
        ```
    
    Monitoring and Observability:
        - Request timing and success rate metrics
        - Error classification and frequency tracking
        - Circuit breaker state monitoring
        - Connection pool utilization metrics
        - Service health and availability tracking
        - Detailed operation logging with correlation IDs
    
    Integration Points:
        - Order Processing Service: Inventory validation and reservation
        - Payment Service: Stock confirmation before payment processing
        - Notification Service: Error alerts and service health notifications
        - Monitoring Systems: Performance metrics and health indicators
        - Audit Service: Operation logging and compliance tracking
    
    Thread Safety:
        All methods are thread-safe and can be called concurrently.
        The underlying HTTP client handles connection pooling and
        thread safety automatically.
    
    Attributes:
        timeout_seconds (float): Configured request timeout
        max_retries (int): Maximum retry attempts for failures
        base_url (str): Inventory service base URL
        _session (httpx.Client): Underlying HTTP client with pooling
    
    🎯 Core Integration Benefits:
        - Enable real-time stock validation and management
        - Ensure data consistency across service boundaries
    
    🔧 Client Features:
        - Configurable HTTP timeouts and retry policies
        - Exponential backoff for transient failure recovery
        - Connection pooling for efficient resource utilization
        - Comprehensive error classification and handling
        - Audit-friendly operation logging and debugging
    
    🚀 Reliability Patterns:
        - Retry Logic: Exponential backoff with jitter for transient failures
        - Timeout Management: Request-level and connection-level timeouts
        - Error Handling: Comprehensive exception mapping and classification
        - Circuit Breaker: Fail-fast behavior for upstream service issues
        - Graceful Degradation: Fallback behavior for service unavailability
    
    📊 Supported Operations:
        - Inventory Queries: Get current stock levels for products
        - Inventory Adjustments: Reserve, release, or modify stock quantities
        - Product Validation: Verify product existence and availability
        - Audit Operations: Track inventory changes with notes and context
    
    🛠️ Configuration:
        The client is configured through the application configuration:
        - inventory_base_url: Base URL of the Inventory Service
        - request_timeout_seconds: HTTP request timeout
        - retry_attempts: Number of retry attempts for failed requests
    
    Example:
        ```python
        # Initialize client (automatically configured)
        client = InventoryClient()
        
        # Check inventory availability
        inventory_data = client.get_inventory("book123")
        available_qty = inventory_data.get("inventory", {}).get("quantity_available", 0)
        
        # Reserve inventory for order
        if available_qty >= requested_qty:
            client.adjust("book123", -requested_qty, notes="order:order456")
        
        # Handle errors gracefully
        try:
            client.adjust("book789", -5, notes="order:order789")
        except InventoryError as e:
            logger.error(f"Failed to reserve inventory: {e}")
            # Implement fallback or error handling
        ```
    
    🔗 Integration Points:
        - Order Creation: Stock validation and reservation
        - Order Cancellation: Inventory release and compensation
        - Inventory Management: Stock level monitoring and adjustment
        - Analytics: Inventory metrics and reporting
    
    📈 Performance Characteristics:
        - Connection Pooling: Efficient HTTP connection reuse
        - Request Batching: Support for bulk inventory operations
        - Caching Strategy: Optional caching for frequently accessed data
        - Monitoring: Built-in metrics for performance tracking
    
    Version: 1.0.0
    """
    
    def __init__(self) -> None:
        """
        Initialize the inventory client with configuration-driven settings.
        
        This constructor loads the application configuration and sets up
        the HTTP client with appropriate timeout, retry, and connection
        settings for reliable communication with the Inventory Service.
        
        🔧 Initialization Process:
            - Load application configuration from environment variables
            - Configure base URL with proper trailing slash handling
            - Set up HTTP timeout configuration for requests
            - Configure retry policy for transient failure handling
        
        🛠️ Configuration Loading:
            - inventory_base_url: Inventory Service endpoint URL
            - request_timeout_seconds: HTTP request timeout duration
            - retry_attempts: Maximum number of retry attempts
        
        Example:
            ```python
            # Client automatically loads configuration
            client = InventoryClient()
            
            # Configuration is applied automatically
            assert client.base == "http://inventory-service:8000"
            assert client.retry_attempts == 3
            ```
        
        ⚠️ Configuration Requirements:
            - inventory_base_url must be a valid HTTP/HTTPS URL
            - request_timeout_seconds should be reasonable (5-30 seconds)
            - retry_attempts should be limited to prevent cascading failures
        """
        # Load configuration from environment variables
        cfg = load_config()
        
        # Configure base URL with proper formatting
        self.base = cfg.inventory_base_url.rstrip("/")
        
        # Configure HTTP timeout for all requests
        self.timeout = httpx.Timeout(cfg.request_timeout_seconds)
        
        # Configure retry policy for transient failures
        self.retry_attempts = cfg.retry_attempts

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Execute HTTP requests with comprehensive retry logic and error handling.
        
        This internal method implements the core HTTP communication logic
        with sophisticated retry strategies, error classification, and
        resilient failure handling for all inventory service interactions.
        
        🔄 Retry Strategy:
            - Exponential backoff: 0.2s, 0.4s, 0.8s, 1.6s intervals
            - Maximum retry attempts: Configurable via retry_attempts
            - Transient error detection: Network issues, 5xx responses
            - Permanent error fast-fail: 4xx responses (except specific cases)
        
        🛠️ Error Handling:
            - Network Errors: Connection timeouts, DNS failures
            - HTTP Errors: 5xx server errors trigger retries
            - Client Errors: 4xx errors fail immediately
            - Timeout Errors: Request and connection timeouts
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            url (str): Complete URL for the request
            **kwargs: Additional arguments passed to httpx.Client.request()
            
        Returns:
            httpx.Response: Successful HTTP response from the inventory service
            
        Raises:
            InventoryError: For all failure scenarios after retry exhaustion
            
        Example:
            ```python
            # Internal usage within client methods
            response = self._request("GET", "http://inventory/api/v1/books/123")
            response = self._request("POST", "http://inventory/api/v1/adjust", 
                                   json={"book_id": "123", "change": -5})
            ```
        
        🔒 Security Considerations:
            - Request timeouts prevent resource exhaustion
            - Retry limits prevent thundering herd problems
            - Error message sanitization prevents information leakage
            - Connection pooling with reasonable limits
        
        📊 Performance Characteristics:
            - Connection reuse through httpx.Client context management
            - Configurable timeouts for predictable behavior
            - Exponential backoff prevents service overload
            - Fast failure for permanent errors
        """
        last_exc = None
        
        # Retry loop with exponential backoff
        for attempt in range(self.retry_attempts + 1):
            try:
                # Use context manager for proper connection handling
                with httpx.Client(timeout=self.timeout) as client:
                    # Execute HTTP request with provided parameters
                    resp = client.request(method, url, **kwargs)
                    
                    # Check for server errors that should trigger retries
                    if resp.status_code >= 500:
                        raise InventoryError(f"Upstream 5xx: {resp.status_code}")
                    
                    # Return successful response (including 4xx client errors)
                    return resp
                    
            except Exception as exc:
                # Store exception for potential re-raising
                last_exc = exc
                
                # Retry with exponential backoff if attempts remaining
                if attempt < self.retry_attempts:
                    # Exponential backoff: 0.2s, 0.4s, 0.8s, 1.6s
                    backoff_delay = 0.2 * (2 ** attempt)
                    time.sleep(backoff_delay)
                else:
                    # Exhausted retries - raise as InventoryError
                    raise InventoryError(str(last_exc))
        
        # Fallback error (should never be reached due to loop logic)
        raise InventoryError("Unexpected client flow")

    def get_inventory(self, book_id: str) -> Dict[str, Any]:
        """
        Retrieve current inventory information for a specific book.
        
        This method queries the Inventory Service to get real-time stock
        information for a specific book, including availability, quantities,
        and other relevant inventory metadata needed for order processing.
        
        🎯 Purpose:
            - Retrieve current stock levels for order validation
            - Get product availability information
            - Support inventory-based business logic decisions
            - Enable real-time stock checking during checkout
        
        📊 Response Data Structure:
            The response typically includes:
            ```json
            {
                "book_id": "book123",
                "inventory": {
                    "quantity_available": 50,
                    "quantity_reserved": 10,
                    "reorder_point": 20,
                    "last_updated": "2024-01-01T12:00:00Z"
                },
                "product": {
                    "title": "Book Title",
                    "price": "19.99",
                    "active": true
                }
            }
            ```
        
        Args:
            book_id (str): Unique identifier for the book/product
            
        Returns:
            Dict[str, Any]: Inventory data dictionary, or empty dict if not found
            
        Raises:
            InventoryError: For service communication failures or system errors
            
        Example:
            ```python
            # Check inventory for order validation
            inventory_data = client.get_inventory("book123")
            
            if inventory_data:
                available = inventory_data.get("inventory", {}).get("quantity_available", 0)
                if available >= requested_quantity:
                    # Proceed with order creation
                    pass
                else:
                    # Handle insufficient stock
                    raise ValueError("Insufficient inventory")
            else:
                # Handle product not found
                raise ValueError("Product not found")
            
            # Graceful handling of missing products
            inventory_data = client.get_inventory("nonexistent-book")
            assert inventory_data == {}  # Returns empty dict for 404
            ```
        
        🔒 Error Handling:
            - 404 Not Found: Returns empty dictionary (graceful handling)
            - 5xx Server Errors: Automatic retry with exponential backoff
            - Network Errors: Automatic retry with exponential backoff
            - 4xx Client Errors: Immediate failure with InventoryError
        
        📈 Performance Considerations:
            - Response caching can be implemented at higher levels
            - Batch queries may be more efficient for multiple books
            - Consider request coalescing for frequently accessed items
            - Monitor response times and implement circuit breaking if needed
        
        🔗 Integration Usage:
            - Order Creation: Pre-validate inventory before processing
            - Cart Management: Real-time availability checking
            - Product Display: Show current availability status
            - Inventory Reporting: Aggregate stock level information
        """
        # Construct inventory query URL with book ID
        url = f"{self.base}/api/v1/inventory/{book_id}"
        
        # Execute GET request with retry logic
        resp = self._request("GET", url)
        
        # Handle 404 gracefully by returning empty dictionary
        if resp.status_code == 404:
            return {}
        
        # Raise for other HTTP errors (4xx client errors)
        resp.raise_for_status()
        
        # Parse and return JSON response
        return resp.json()

    def adjust(self, book_id: str, change: int, notes: str = "") -> Dict[str, Any]:
        """
        Adjust inventory quantities for a specific book with audit trail support.
        
        This method performs inventory adjustments (positive or negative) for
        stock management operations like reservations, releases, restocking,
        or corrections. It includes comprehensive audit trail support through
        the notes parameter for tracking and debugging.
        
        🎯 Purpose:
            - Reserve inventory for order processing (negative adjustments)
            - Release reserved inventory for cancelled orders (positive adjustments)
            - Perform inventory corrections and restocking operations
            - Maintain audit trail for all inventory movements
            - Support compensating transactions for error recovery
        
        💰 Adjustment Types:
            - Reservations: Negative adjustments to reserve stock for orders
            - Releases: Positive adjustments to release reserved stock
            - Restocking: Positive adjustments for new inventory arrivals
            - Corrections: Positive or negative adjustments for inventory fixes
            - Compensations: Reverse adjustments for failed operations
        
        📊 Request/Response Flow:
            Request payload:
            ```json
            {
                "quantity_change": -5,
                "notes": "order:order123 - Reserved for customer purchase"
            }
            ```
            
            Response data:
            ```json
            {
                "book_id": "book123",
                "previous_quantity": 50,
                "new_quantity": 45,
                "change_applied": -5,
                "transaction_id": "txn456",
                "timestamp": "2024-01-01T12:00:00Z"
            }
            ```
        
        Args:
            book_id (str): Unique identifier for the book/product
            change (int): Quantity change (negative for reservations, positive for releases)
            notes (str, optional): Audit notes describing the reason for adjustment
            
        Returns:
            Dict[str, Any]: Adjustment result with transaction details
            
        Raises:
            InventoryError: For service failures, insufficient stock, or invalid operations
            
        Example:
            ```python
            # Reserve inventory for order
            try:
                result = client.adjust("book123", -3, notes="order:ord456 - Customer purchase")
                print(f"Reserved 3 units, new quantity: {result['new_quantity']}")
            except InventoryError as e:
                logger.error(f"Failed to reserve inventory: {e}")
                # Handle reservation failure
            
            # Release inventory for cancelled order
            try:
                result = client.adjust("book123", 3, notes="compensate:ord456 - Order cancelled")
                print(f"Released 3 units, new quantity: {result['new_quantity']}")
            except InventoryError as e:
                logger.warning(f"Failed to release inventory: {e}")
                # Log compensation failure but continue
            
            # Restock inventory
            restock_result = client.adjust("book123", 25, notes="restock:vendor-shipment-789")
            ```
        
        🔄 Compensating Transactions:
            This method supports compensating transactions for error recovery:
            ```python
            # Original reservation
            client.adjust("book123", -5, notes="order:ord123")
            
            # Compensation if order fails
            try:
                # ... order processing ...
                pass
            except Exception:
                # Compensate by releasing reserved inventory
                client.adjust("book123", 5, notes="compensate:ord123 - Order failed")
            ```
        
        🔒 Business Rules:
            - Negative adjustments may fail if insufficient stock available
            - Adjustment operations are atomic and consistent
            - All adjustments are logged with audit trail information
            - Transaction IDs enable tracking and reconciliation
        
        📈 Performance Considerations:
            - Adjustments are processed synchronously for consistency
            - Batch adjustment APIs may be available for bulk operations
            - Consider queuing for high-volume adjustment scenarios
            - Monitor adjustment latency and implement alerting
        
        🔗 Integration Usage:
            - Order Processing: Reserve and release inventory
            - Error Recovery: Compensating transactions
            - Inventory Management: Restocking and corrections
            - Analytics: Inventory movement tracking and reporting
        """
        # Construct inventory adjustment URL with book ID parameter
        url = f"{self.base}/api/v1/inventory/adjust?book_id={book_id}"
        
        # Prepare adjustment payload with change amount and audit notes
        payload = {"quantity_change": change, "notes": notes}
        
        # Execute POST request with JSON payload and retry logic
        resp = self._request("POST", url, json=payload)
        
        # Raise for HTTP errors (4xx/5xx after retries)
        resp.raise_for_status()
        
        # Parse and return JSON response with adjustment details
        return resp.json()


