"""Database connection and session management."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from ..utils.config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Database:
    """Database connection manager."""
    
    _engine = None
    _session_factory = None
    
    @classmethod
    def initialize(cls, database_url: str = None):
        """Initialize database connection.
        
        Args:
            database_url: Database connection string (uses config if not provided)
        """
        if cls._engine is not None:
            return
        
        db_url = database_url or config.database_url
        logger.info(f"Initializing database connection: {db_url}")
        
        # SQLite specific settings
        if db_url.startswith("sqlite"):
            cls._engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
            
            # Enable foreign keys for SQLite
            @event.listens_for(cls._engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        else:
            cls._engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        
        cls._session_factory = sessionmaker(
            bind=cls._engine,
            autocommit=False,
            autoflush=False
        )
        
        logger.info("Database connection initialized successfully")
    
    @classmethod
    def create_tables(cls):
        """Create all tables in the database."""
        if cls._engine is None:
            cls.initialize()
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(cls._engine)
        logger.info("Database tables created successfully")
    
    @classmethod
    def drop_tables(cls):
        """Drop all tables in the database."""
        if cls._engine is None:
            cls.initialize()
        
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(cls._engine)
        logger.info("Database tables dropped successfully")
    
    @classmethod
    @contextmanager
    def get_session(cls) -> Generator:
        """Get a database session with automatic cleanup.
        
        Yields:
            SQLAlchemy session
        """
        if cls._session_factory is None:
            cls.initialize()
        
        session = cls._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @classmethod
    def get_engine(cls):
        """Get the database engine."""
        if cls._engine is None:
            cls.initialize()
        return cls._engine


# Convenience function
def get_session():
    """Get a database session."""
    return Database.get_session()
