import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (parent of app/) so it works regardless of cwd
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_SECRET = os.getenv("X_ACCESS_SECRET")

MATCH_LOOP_SECONDS = 30
MIN_POST_DELAY = 5
MAX_POST_DELAY = 25
