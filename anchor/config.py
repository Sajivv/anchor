import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ANCHOR_DATA_DIR = BASE_DIR / "anchor_data"
DATABASE_PATH = ANCHOR_DATA_DIR / "db.json"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_REASONING_MODEL = os.environ.get("OPENAI_REASONING_MODEL", "gpt-5.3-codex")
OPENAI_REASONING_EFFORT = os.environ.get("OPENAI_REASONING_EFFORT", "medium")
ANCHOR_REASONING_BACKEND = os.environ.get(
    "ANCHOR_REASONING_BACKEND",
    "openai" if OPENAI_API_KEY else "mock",
)
