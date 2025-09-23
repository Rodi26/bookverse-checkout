
"""
BookVerse Checkout Service - Database Management Module

This module provides comprehensive database management functionality for the
BookVerse Checkout Service, including connection handling, session management,
and transaction control with SQLAlchemy ORM integration.

🏗️ Architecture Overview:
    The module implements a robust database layer with these components:
    - Engine Management: Database connection and configuration
    - Session Factory: Context-managed database session creation
    - Transaction Control: Automatic commit/rollback handling
    - Connection Pooling: Efficient database connection management
    - Thread Safety: SQLite compatibility for development environments

🚀 Key Features:
    - Lazy initialization of database connections
    - Context manager pattern for session management
    - Automatic transaction handling with proper rollback
    - Support for both SQLite (development) and PostgreSQL (production)
    - Thread-safe session management
    - Connection pooling for optimal performance

🔧 Database Configuration:
    - Engine: SQLAlchemy engine with configurable connection parameters
    - Sessions: Factory pattern for database session creation
    - Transactions: Explicit transaction control with automatic cleanup
    - Connection Management: Automatic connection pooling and cleanup

📊 Usage Patterns:
    The module supports two primary usage patterns:
    
    1. Context Manager (Recommended):
        ```python
        with session_scope() as session:
            order = Order(customer_id="user123", total=29.99)
            session.add(order)
            # Automatic commit on success, rollback on exception
        ```
    
    2. Manual Session Management:
        ```python
        session = get_session()
        try:
            order = session.query(Order).filter_by(id=order_id).first()
            session.commit()
        finally:
            session.close()
        ```

🛠️ Development Usage:
    Database initialization and management:
    ```python
    # Initialize database (called during app startup)
    create_all()
    
    # Use database session in service methods
    with session_scope() as db:
        orders = db.query(Order).filter_by(customer_id=customer_id).all()
        return orders
    ```

📋 Dependencies:
    Core dependencies for database operations:
    - SQLAlchemy: ORM and database abstraction layer
    - SQLite: Embedded database for development and testing
    - PostgreSQL: Production database (via psycopg2)
    - contextlib: Context manager utilities for session handling

⚠️ Important Notes:
    - Engine initialization is lazy and happens on first database access
    - All sessions use explicit transaction control (autocommit=False)
    - SQLite uses check_same_thread=False for FastAPI compatibility
    - Connection pooling is managed automatically by SQLAlchemy
    - Sessions must be properly closed to prevent connection leaks

🔒 Security Considerations:
    - Database connection strings should not contain credentials in logs
    - SQLite is suitable for development but not production scale
    - Connection pooling prevents connection exhaustion attacks
    - Transaction isolation prevents race conditions

📊 Performance Characteristics:
    - SQLite: Suitable for development and small-scale deployments
    - PostgreSQL: Production-ready with connection pooling
    - Session lifecycle: Short-lived sessions for web request patterns
    - Connection management: Automatic pooling and cleanup

Authors: BookVerse Platform Team
Version: 1.0.0
Last Updated: 2024-01-01
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from .config import load_config

# SQLAlchemy declarative base for model definitions
Base = declarative_base()

# Global database connection components (initialized lazily)
_engine = None  # SQLAlchemy engine for database connection
_SessionLocal = None  # Session factory for creating database sessions


def init_engine() -> None:
    """
    Initialize the SQLAlchemy engine and session factory.
    
    This function sets up the database connection engine and session factory
    based on the configuration loaded from environment variables. It supports
    both SQLite (for development) and PostgreSQL (for production) databases
    with appropriate connection parameters.
    
    🔧 Configuration:
        - Database URL from configuration (supports SQLite and PostgreSQL)
        - SQLite: Uses check_same_thread=False for FastAPI compatibility
        - PostgreSQL: Uses default connection pooling settings
        - Future mode enabled for SQLAlchemy 2.0 compatibility
    
    🚀 Connection Features:
        - Connection pooling for efficient resource usage
        - Automatic connection management and cleanup
        - Thread-safe operation for concurrent requests
        - Lazy loading - only connects when needed
    
    ⚠️ Important Notes:
        - Called automatically when first database operation is performed
        - Global variables are used for singleton pattern implementation
        - Session factory is configured with explicit transaction control
        - Future=True enables SQLAlchemy 2.0 compatibility mode
    
    Example:
        ```python
        # Usually called automatically, but can be called explicitly
        init_engine()
        
        # Engine and session factory are now available globally
        with session_scope() as db:
            # Database operations here
            pass
        ```
    
    Raises:
        SQLAlchemyError: If database connection cannot be established
        ConfigurationError: If database URL is invalid or missing
    """
    global _engine, _SessionLocal
    
    # Load configuration from environment variables
    cfg = load_config()
    
    # Configure connection arguments based on database type
    connect_args = {}
    if cfg.database_url.startswith("sqlite"):
        # SQLite-specific configuration for FastAPI compatibility
        connect_args = {"check_same_thread": False}
    
    # Create SQLAlchemy engine with appropriate configuration
    _engine = create_engine(
        cfg.database_url,
        connect_args=connect_args,
        future=True  # Enable SQLAlchemy 2.0 compatibility
    )
    
    # Create session factory with explicit transaction control
    _SessionLocal = sessionmaker(
        bind=_engine,
        autoflush=False,    # Disable automatic flushing for explicit control
        autocommit=False,   # Disable autocommit for explicit transaction management
        future=True         # Enable SQLAlchemy 2.0 compatibility
    )


def create_all() -> None:
    """
    Create all database tables defined by SQLAlchemy models.
    
    This function ensures that all database tables corresponding to the
    SQLAlchemy models (derived from Base) are created in the database.
    It's typically called during application startup to initialize the
    database schema.
    
    🏗️ Table Creation Process:
        - Initializes engine if not already done
        - Creates all tables defined in model classes
        - Handles both SQLite and PostgreSQL table creation
        - Idempotent operation (safe to call multiple times)
    
    🔧 Schema Management:
        - Creates tables based on SQLAlchemy model definitions
        - Handles foreign key relationships and constraints
        - Creates indexes defined in model classes
        - Supports both development and production database schemas
    
    ⚠️ Important Notes:
        - Should be called during application startup
        - Safe to call multiple times (won't recreate existing tables)
        - Does not handle schema migrations (use Alembic for production)
        - In production, consider using proper migration tools
    
    Example:
        ```python
        # Called during application startup
        create_all()
        
        # Now all model tables exist in the database
        with session_scope() as db:
            # Can now perform operations on all model tables
            orders = db.query(Order).all()
        ```
    
    Raises:
        SQLAlchemyError: If table creation fails
        DatabaseError: If database is not accessible
    """
    # Ensure engine is initialized before table creation
    if _engine is None:
        init_engine()
    
    # Create all tables defined by model classes
    Base.metadata.create_all(bind=_engine)


@contextmanager
def session_scope() -> Session:
    """
    Provide a transactional scope around a series of database operations.
    
    This context manager creates a new database session, yields it for use,
    and ensures proper transaction handling with automatic commit on success
    or rollback on exception. This is the recommended pattern for database
    operations in the checkout service.
    
    🔄 Transaction Lifecycle:
        1. Creates new session from session factory
        2. Yields session for database operations
        3. Commits transaction if no exceptions occur
        4. Rolls back transaction if exceptions are raised
        5. Always closes session to release resources
    
    🚀 Key Benefits:
        - Automatic transaction management (commit/rollback)
        - Guaranteed resource cleanup (session.close())
        - Exception safety with proper rollback handling
        - Context manager pattern for clean code
        - Thread-safe session management
    
    🛠️ Usage Examples:
        Basic order creation:
        ```python
        with session_scope() as db:
            order = Order(
                customer_id="user123",
                total_amount=Decimal("29.99"),
                status="pending"
            )
            db.add(order)
            # Automatic commit when exiting context
        ```
        
        Query with error handling:
        ```python
        try:
            with session_scope() as db:
                orders = db.query(Order).filter_by(
                    customer_id=customer_id
                ).all()
                # Process orders
                for order in orders:
                    order.status = "processed"
                # Automatic commit
        except SQLAlchemyError as e:
            # Transaction automatically rolled back
            logger.error(f"Database error: {e}")
        ```
        
        Complex multi-table operations:
        ```python
        with session_scope() as db:
            # Create order
            order = Order(customer_id="user123", total=50.00)
            db.add(order)
            db.flush()  # Get order ID without committing
            
            # Create order items
            for item_data in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    book_id=item_data['book_id'],
                    quantity=item_data['quantity']
                )
                db.add(order_item)
            
            # All operations committed together
        ```
    
    ⚠️ Important Notes:
        - Session is automatically closed even if exceptions occur
        - Nested transactions are not supported with this pattern
        - Each context creates a new session (not shared across contexts)
        - Lazy initialization of engine happens on first call
        - Sessions should not be stored or used outside the context
    
    Yields:
        Session: SQLAlchemy database session for performing operations
    
    Raises:
        SQLAlchemyError: Database operation errors (after rollback)
        Exception: Any other exceptions (after rollback and session cleanup)
    """
    # Ensure session factory is initialized
    if _SessionLocal is None:
        init_engine()
    
    # Create new session from factory
    session = _SessionLocal()
    
    try:
        # Yield session for database operations
        yield session
        
        # Commit transaction if no exceptions occurred
        session.commit()
        
    except Exception:
        # Rollback transaction on any exception
        session.rollback()
        
        # Re-raise the exception for caller to handle
        raise
        
    finally:
        # Always close session to release resources
        session.close()


