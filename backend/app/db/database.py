"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.utils.config import get_settings

settings = get_settings()

# Create engine
# Use SQLite for local demo if Postgres not available
database_url = settings.database_url
if "postgresql" in database_url and "localhost" in database_url:
    # Check if we can connect to Postgres, fallback to SQLite
    try:
        import psycopg2
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        conn = psycopg2.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            user=parsed.username or "postgres",
            password=parsed.password or "postgres",
            database=parsed.path[1:] if parsed.path else "jobdb",
            connect_timeout=2
        )
        conn.close()
    except:
        # Fallback to SQLite for demo
        database_url = "sqlite:///./jobdb.db"
        print("⚠️  Postgres not available, using SQLite for demo")

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

