"""
Database connection and operations module
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from backend.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """Initialize the database with tables"""
    from backend.models.base import Base
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db_session() -> Session:
    """Get a database session"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_db() -> Session:
    """Dependency for FastAPI to get DB session"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
