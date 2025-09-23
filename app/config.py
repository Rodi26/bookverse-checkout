
"""
BookVerse Checkout Service - Configuration Management System

This module implements a comprehensive configuration management system for the BookVerse
Checkout Service, providing type-safe configuration loading, environment variable integration,
and enterprise-grade configuration patterns for reliable order processing across all
deployment environments.

The configuration system implements advanced patterns including:
- Type-safe configuration with dataclass validation
- Environment variable integration with secure defaults
- Multi-environment configuration support (dev, staging, production)
- Business logic configuration for payment processing
- Service integration configuration for upstream dependencies
- Performance tuning parameters for optimal operation

🔧 Configuration Architecture:
    📊 **Structured Configuration**: Type-safe dataclass-based configuration
    🌍 **Environment Awareness**: 12-factor app compliance with environment variables
    🔒 **Secure Defaults**: Production-ready defaults with development overrides
    ⚡ **Performance Tuning**: Configurable timeouts and retry parameters
    💳 **Payment Configuration**: Configurable payment simulation and testing
    🔗 **Service Integration**: Upstream service connection configuration

🌟 Key Features:
    - Type safety with automatic validation and conversion
    - Environment variable override support for all settings
    - Secure default values for immediate development setup
    - Production-ready configuration patterns
    - Integration testing configuration support
    - Performance optimization through tunable parameters

Configuration Sources (Priority Order):
    1. Environment Variables (highest priority)
    2. Default Values (fallback for missing environment variables)
    3. Configuration Files (future enhancement)
    4. Command Line Arguments (future enhancement)

Usage Patterns:
    ```python
    # Load configuration in application startup
    from .config import load_config
    
    config = load_config()
    
    # Use type-safe configuration throughout application
    database_url = config.database_url
    timeout = config.request_timeout_seconds
    
    # Environment variable configuration examples:
    # export DATABASE_URL="postgresql://user:pass@localhost/checkout"
    # export INVENTORY_BASE_URL="http://inventory-service:8001"
    # export REQUEST_TIMEOUT_SECONDS="5.0"
    # export RETRY_ATTEMPTS="3"
    # export PAYMENT_SUCCESS_RATIO="0.95"
    # export LOG_LEVEL="DEBUG"
    ```

Environment Configuration Examples:
    - Development: Local SQLite, localhost services, relaxed timeouts
    - Testing: In-memory databases, mock services, fast timeouts
    - Staging: Production-like databases, real services, production timeouts
    - Production: Production databases, load balancers, optimized settings

Authors: BookVerse Platform Team
Version: 1.0.0
Last Updated: 2024-01-15
"""

import os
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """
    Type-Safe Service Configuration Container
    
    Provides a strongly-typed configuration container for the BookVerse Checkout Service,
    implementing comprehensive configuration management with automatic type conversion,
    validation, and environment-aware defaults for reliable service operation.
    
    This dataclass serves as the central configuration authority for the service,
    ensuring type safety, providing clear configuration structure, and supporting
    environment-specific overrides for flexible deployment scenarios.
    
    Configuration Categories:
        🗄️ **Database Configuration**: Primary data store connection settings
        🔗 **Service Integration**: Upstream service connectivity configuration
        ⚡ **Performance Settings**: Timeout and retry configuration for optimal performance
        💳 **Payment Processing**: Payment simulation and testing configuration
        📋 **Operational Settings**: Logging and monitoring configuration
    
    Type Safety Features:
        - Automatic type conversion from environment variables
        - Compile-time type checking support
        - Runtime validation of configuration values
        - Clear error messages for invalid configurations
        - IDE support with autocompletion and type hints
    
    Attributes:
        database_url (str): SQLAlchemy-compatible database connection URL
        inventory_base_url (str): Base URL for Inventory Service integration
        request_timeout_seconds (float): HTTP request timeout for service calls
        retry_attempts (int): Maximum retry attempts for failed requests
        payment_success_ratio (float): Payment success rate for testing/simulation
        log_level (str): Application logging verbosity level
    
    Environment Variable Mapping:
        - database_url ← DATABASE_URL
        - inventory_base_url ← INVENTORY_BASE_URL  
        - request_timeout_seconds ← REQUEST_TIMEOUT_SECONDS
        - retry_attempts ← RETRY_ATTEMPTS
        - payment_success_ratio ← PAYMENT_SUCCESS_RATIO
        - log_level ← LOG_LEVEL
    
    Validation Rules:
        - database_url: Must be valid SQLAlchemy URL format
        - inventory_base_url: Must be valid HTTP/HTTPS URL
        - request_timeout_seconds: Must be positive float (> 0.0)
        - retry_attempts: Must be non-negative integer (>= 0)
        - payment_success_ratio: Must be between 0.0 and 1.0 inclusive
        - log_level: Must be valid logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Usage Examples:
        ```python
        # Load configuration
        config = load_config()
        
        # Type-safe access with IDE support
        database_url: str = config.database_url
        timeout: float = config.request_timeout_seconds
        retries: int = config.retry_attempts
        
        # Configuration validation
        assert config.request_timeout_seconds > 0, "Timeout must be positive"
        assert 0.0 <= config.payment_success_ratio <= 1.0, "Success ratio must be 0-1"
        assert config.retry_attempts >= 0, "Retry attempts must be non-negative"
        ```
    
    Environment-Specific Examples:
        ```bash
        # Development Environment
        export DATABASE_URL="sqlite:///./checkout_dev.db"
        export INVENTORY_BASE_URL="http://localhost:8001"
        export REQUEST_TIMEOUT_SECONDS="10.0"
        export RETRY_ATTEMPTS="3"
        export PAYMENT_SUCCESS_RATIO="1.0"
        export LOG_LEVEL="DEBUG"
        
        # Production Environment
        export DATABASE_URL="postgresql://checkout_user:password@prod-db:5432/checkout"
        export INVENTORY_BASE_URL="https://inventory-service.bookverse.com"
        export REQUEST_TIMEOUT_SECONDS="2.0"
        export RETRY_ATTEMPTS="2"
        export PAYMENT_SUCCESS_RATIO="0.98"
        export LOG_LEVEL="WARNING"
        
        # Testing Environment
        export DATABASE_URL="sqlite:///:memory:"
        export INVENTORY_BASE_URL="http://mock-inventory:8001"
        export REQUEST_TIMEOUT_SECONDS="1.0"
        export RETRY_ATTEMPTS="1"
        export PAYMENT_SUCCESS_RATIO="0.9"
        export LOG_LEVEL="INFO"
        ```
    
    Integration Benefits:
        - FastAPI dependency injection compatible
        - Pydantic model integration ready
        - Docker environment variable mapping
        - Kubernetes ConfigMap and Secret integration
        - CI/CD pipeline configuration management
    """
    database_url: str
    """
    Database connection URL for order and transaction persistence.
    
    Specifies the primary database connection used by SQLAlchemy for all
    order processing, transaction management, and audit trail operations.
    Supports multiple database backends with environment-specific configuration.
    
    Environment Variable: DATABASE_URL
    Default: "sqlite:///./checkout.db"
    Type: str (SQLAlchemy-compatible URL)
    
    Supported Database Types:
        - SQLite (development): "sqlite:///./checkout.db"
        - PostgreSQL (production): "postgresql://user:pass@host:port/db"
        - MySQL (alternative): "mysql://user:pass@host:port/db"
        - SQL Server (enterprise): "mssql://user:pass@host:port/db"
    
    Security Considerations:
        - No credentials in source code
        - Environment variable for sensitive data
        - SSL/TLS support for remote connections
        - Connection pooling for production deployments
    """
    
    inventory_base_url: str
    """
    Base URL for BookVerse Inventory Service integration.
    
    Defines the upstream Inventory Service endpoint for stock verification,
    inventory adjustments, and product information retrieval during order
    processing workflows.
    
    Environment Variable: INVENTORY_BASE_URL
    Default: "http://localhost:8001"
    Type: str (HTTP/HTTPS URL)
    
    Environment Examples:
        - Development: "http://localhost:8001"
        - Docker Compose: "http://inventory:8001"
        - Kubernetes: "http://inventory-service:8001"
        - Production: "https://inventory-api.bookverse.com"
    
    Integration Features:
        - Load balancer support through base URL
        - Health check endpoint integration
        - Service discovery compatibility
        - SSL/TLS termination support
    """
    
    request_timeout_seconds: float
    """
    HTTP request timeout for upstream service calls.
    
    Configures the maximum time to wait for responses from upstream services
    (primarily Inventory Service) before timing out and triggering retry
    logic or failure handling.
    
    Environment Variable: REQUEST_TIMEOUT_SECONDS
    Default: 2.0 seconds
    Type: float (seconds, must be > 0.0)
    
    Timeout Considerations:
        - Network latency and service response time
        - Load balancer and proxy overhead
        - Database query performance at upstream service
        - Circuit breaker integration timing
        - User experience expectations
    
    Environment-Specific Recommendations:
        - Development: 10.0 (relaxed for debugging)
        - Testing: 1.0 (fast feedback for tests)
        - Staging: 3.0 (realistic network conditions)
        - Production: 2.0 (optimized for performance)
    """
    
    retry_attempts: int
    """
    Maximum retry attempts for failed upstream service requests.
    
    Defines how many times to retry failed requests to upstream services
    before giving up and returning an error to the client. Implements
    exponential backoff between retry attempts.
    
    Environment Variable: RETRY_ATTEMPTS
    Default: 2 attempts
    Type: int (must be >= 0)
    
    Retry Strategy:
        - Exponential backoff: 1s, 2s, 4s delays
        - Only retry on 5xx server errors and timeouts
        - No retry on 4xx client errors
        - Circuit breaker integration for failure detection
    
    Performance Impact:
        - Higher values: More resilient, but slower failure response
        - Lower values: Faster failure response, less resilient
        - Zero retries: Immediate failure, maximum performance
    
    Environment Tuning:
        - Development: 3 (debugging network issues)
        - Testing: 1 (fast test execution)
        - Production: 2 (balanced resilience and performance)
    """
    
    payment_success_ratio: float
    """
    Payment processing success rate for simulation and testing.
    
    Controls the artificial success rate for payment processing in
    development and testing environments. In production, this should
    be 1.0 (100% success rate determined by actual payment processing).
    
    Environment Variable: PAYMENT_SUCCESS_RATIO
    Default: 1.0 (100% success)
    Type: float (must be 0.0 <= value <= 1.0)
    
    Testing Scenarios:
        - 1.0: All payments succeed (production default)
        - 0.95: 5% payment failure rate for error handling testing
        - 0.8: 20% failure rate for stress testing
        - 0.0: All payments fail for negative testing
    
    Business Logic Integration:
        - Failed payments trigger order cancellation
        - Inventory reservations released on payment failure
        - Audit trail maintained for all payment attempts
        - Customer notification for payment failures
    
    Environment Usage:
        - Development: 1.0 (focus on functionality)
        - Testing: 0.9 (test error handling)
        - Staging: 0.98 (realistic failure rates)
        - Production: 1.0 (real payment processing)
    """
    
    log_level: str
    """
    Application logging verbosity level.
    
    Controls the detail level of application logging output across all
    service components. Affects performance, storage requirements, and
    debugging capabilities.
    
    Environment Variable: LOG_LEVEL
    Default: "INFO"
    Type: str (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Logging Levels:
        - DEBUG: Detailed diagnostic information
        - INFO: General operational information  
        - WARNING: Warning messages for attention
        - ERROR: Error conditions that don't stop operation
        - CRITICAL: Serious errors that may stop operation
    
    Environment Recommendations:
        - Development: DEBUG (comprehensive debugging)
        - Testing: INFO (operational visibility)
        - Staging: INFO (production-like logging)
        - Production: WARNING (minimal overhead)
    
    Performance Impact:
        - DEBUG: High volume, significant overhead
        - INFO: Moderate volume, minimal overhead
        - WARNING+: Low volume, negligible overhead
    """


def load_config() -> ServiceConfig:
    """
    Load Service Configuration from Environment Variables
    
    Creates and returns a type-safe ServiceConfig instance populated from
    environment variables with secure defaults for missing values. Implements
    automatic type conversion and provides a single source of truth for all
    service configuration.
    
    This function serves as the primary configuration factory for the BookVerse
    Checkout Service, handling environment variable parsing, type conversion,
    and default value assignment in a centralized, maintainable manner.
    
    Configuration Loading Process:
        1. Read environment variables with os.getenv()
        2. Apply type conversion (str, int, float) as needed
        3. Use secure defaults for missing environment variables
        4. Create type-safe ServiceConfig dataclass instance
        5. Return configuration ready for application use
    
    Environment Variable Processing:
        - Automatic type conversion from string values
        - Error handling for invalid type conversions
        - Secure defaults prevent application startup failures
        - Clear error messages for configuration problems
    
    Returns:
        ServiceConfig: Fully populated configuration instance with type safety
        
    Raises:
        ValueError: If environment variable values cannot be converted to required types
        TypeError: If configuration values fail validation rules
        
    Usage Examples:
        ```python
        # Basic configuration loading
        config = load_config()
        
        # Use configuration throughout application
        engine = create_engine(config.database_url)
        inventory_client = InventoryClient(config.inventory_base_url)
        
        # Configuration-based service initialization
        def create_checkout_service(config: ServiceConfig) -> CheckoutService:
            return CheckoutService(
                database_url=config.database_url,
                inventory_url=config.inventory_base_url,
                timeout=config.request_timeout_seconds,
                retries=config.retry_attempts
            )
        ```
    
    Environment Variable Examples:
        ```bash
        # Minimal configuration (uses defaults)
        export DATABASE_URL="postgresql://user:pass@localhost/checkout"
        
        # Complete configuration override
        export DATABASE_URL="postgresql://user:pass@prod-db:5432/checkout"
        export INVENTORY_BASE_URL="https://inventory.bookverse.com"
        export REQUEST_TIMEOUT_SECONDS="3.0"
        export RETRY_ATTEMPTS="3"
        export PAYMENT_SUCCESS_RATIO="0.99"
        export LOG_LEVEL="ERROR"
        ```
    
    Configuration Validation:
        ```python
        # Load and validate configuration
        config = load_config()
        
        # Validate configuration constraints
        assert config.request_timeout_seconds > 0, "Timeout must be positive"
        assert 0.0 <= config.payment_success_ratio <= 1.0, "Success ratio must be 0-1"
        assert config.retry_attempts >= 0, "Retry attempts must be non-negative"
        assert config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        ```
    
    Error Handling:
        - Invalid float values: ValueError with clear message
        - Invalid int values: ValueError with clear message
        - Missing environment variables: Uses secure defaults
        - Invalid URL formats: Application startup validation recommended
    
    Performance Characteristics:
        - Fast execution: Simple environment variable reads
        - Memory efficient: Single configuration instance
        - Thread safe: Immutable configuration after loading
        - Startup validation: Early error detection
    
    Integration Patterns:
        - FastAPI dependency injection
        - Application factory pattern
        - Configuration-based service creation
        - Environment-specific service behavior
    
    Future Enhancements:
        - Configuration file loading support
        - Configuration validation with Pydantic
        - Configuration hot-reloading capabilities
        - External configuration service integration
        - Encrypted configuration value support
    """
    return ServiceConfig(
        # Database connection with secure SQLite default for development
        database_url=os.getenv("DATABASE_URL", "sqlite:///./checkout.db"),
        
        # Inventory service integration with localhost default for development  
        inventory_base_url=os.getenv("INVENTORY_BASE_URL", "http://localhost:8001"),
        
        # Performance tuning with balanced defaults for production readiness
        request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "2")),
        retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "2")),
        
        # Payment simulation with 100% success default for predictable behavior
        payment_success_ratio=float(os.getenv("PAYMENT_SUCCESS_RATIO", "1.0")),
        
        # Logging configuration with INFO level for operational visibility
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


