import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Build an absolute path to the project's root directory
# (this file is in .../backend/app/core, so we go up 3 levels)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Load the .env file from the project root
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Define the default SQLite path *in the project root*
DEFAULT_SQLITE_URL = f"sqlite:///{os.path.join(PROJECT_ROOT, 'diningbot.db')}"

# Get DATABASE_URL from .env, or use our new absolute default if it's not set
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
