import os
import threading
import logging
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Load environment variables from backend/.env (relative to this file)
backend_dir = Path(__file__).resolve().parents[2]
env_path = backend_dir / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        f"DATABASE_URL not found in environment variables. Please create {env_path} with DATABASE_URL set."
    )

# dev/prod toggle (set DEV_MODE=1 in .env for local dev to avoid client-side pools)
DEV_MODE = os.getenv("DEV_MODE", "0") == "1"

# Create a single engine per process. Use NullPool in dev to avoid long-lived client pools
print(f"[db] loading DB module pid={os.getpid()} DEV_MODE={DEV_MODE}")
if DEV_MODE:
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo_pool=True,
        pool_pre_ping=True,
    )
else:
    # Conservative pool sizing for Supabase session mode (port 5432)
    engine = create_engine(
    DATABASE_URL,
    pool_size=2,
    max_overflow=0,
    pool_timeout=5,  # seconds
)


# Session factory and base declarative
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# lightweight event listeners to log checkouts/checkins for diagnostics
logger = logging.getLogger("sqlalchemy.pool")
logger.setLevel(logging.INFO)

@event.listens_for(engine, "checkout")
def _on_checkout(dbapi_con, con_record, con_proxy):
    print(f"[db][pool] checkout pid={os.getpid()} thread={threading.get_ident()}")

@event.listens_for(engine, "checkin")
def _on_checkin(dbapi_con, con_record):
    print(f"[db][pool] checkin pid={os.getpid()} thread={threading.get_ident()}")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and ensures it is closed.

    Import `get_db` from `app.core.database` in route modules and use as
    `Depends(get_db)` so all sessions come from this central session factory.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()