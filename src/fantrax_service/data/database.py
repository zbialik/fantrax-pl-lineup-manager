"""Database connection and session management."""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator

from fantrax_service.config import Config

logger = logging.getLogger(__name__)

Base = declarative_base()

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        database_url = Config.DATABASE_URL
        # Handle SQLite special case
        if database_url.startswith("sqlite"):
            # Enable foreign keys for SQLite
            _engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                echo=False
            )
        else:
            _engine = create_engine(database_url, echo=False)
        logger.info(f"Database engine created for: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Get a database session context manager."""
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope():
    """Context manager for database sessions."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize the database by creating all tables."""
    from fantrax_service.data.models import PlayerModel, PlayerStatsModel, SyncLogModel
    Base.metadata.create_all(bind=get_engine())
    logger.info("Database tables created/verified")


def drop_db():
    """Drop all database tables (use with caution!)."""
    Base.metadata.drop_all(bind=get_engine())
    logger.warning("All database tables dropped")

