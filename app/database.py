"""Database connection and session management."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.config import settings
from app.models.base import Base
import logging

logger = logging.getLogger(__name__)

# Connection pooling configuration
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Test connections before using
    echo=settings.SQLALCHEMY_ECHO,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

def drop_all_tables():
    """Drop all tables (development only)."""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")

# Connection event listeners
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Set PostgreSQL connection options."""
    try:
        # Enable JSONB operators
        cursor = dbapi_conn.cursor()
        cursor.execute("SET jit = off")  # Disable JIT for better performance on small queries
        cursor.close()
    except Exception as e:
        logger.error(f"Failed to set connection options: {e}")
