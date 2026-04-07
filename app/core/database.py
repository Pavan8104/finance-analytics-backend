from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# ---------------------------------------------------------------------------
# Detect database dialect
# ---------------------------------------------------------------------------
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# SQLite requires check_same_thread=False for multi-threaded FastAPI
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    # pool_pre_ping sends a lightweight test query before returning a
    # connection from the pool — silently handles stale connections
    pool_pre_ping=True,
    # Echo SQL in development for easier debugging
    echo=settings.ENVIRONMENT == "development",
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# Declarative base — all models must inherit from this
# ---------------------------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    """
    Yields a SQLAlchemy session, ensuring it is closed after the request
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
