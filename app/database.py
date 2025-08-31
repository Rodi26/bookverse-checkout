"""
Database setup for Checkout (SQLite for demo).
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from .config import load_config


Base = declarative_base()

_engine = None
_SessionLocal = None


def init_engine() -> None:
    global _engine, _SessionLocal
    cfg = load_config()
    connect_args = {"check_same_thread": False} if cfg.database_url.startswith("sqlite") else {}
    _engine = create_engine(cfg.database_url, connect_args=connect_args, future=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


def create_all() -> None:
    if _engine is None:
        init_engine()
    Base.metadata.create_all(bind=_engine)


@contextmanager
def session_scope() -> Session:
    if _SessionLocal is None:
        init_engine()
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


