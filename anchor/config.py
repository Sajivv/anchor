from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ANCHOR_DATA_DIR = BASE_DIR / "anchor_data"
DATABASE_PATH = ANCHOR_DATA_DIR / "db.json"
