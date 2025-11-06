import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from backend directory
backend_dir = Path(__file__).parent.parent.parent
env_path = backend_dir / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
