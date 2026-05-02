import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_CACHE_DIR = BASE_DIR / "marlin_cache"
MISSION_CONFIG_PATH = LOCAL_CACHE_DIR / "mission_config.json"
NODE_STATE_PATH = LOCAL_CACHE_DIR / "node_state.json"
OUTBOUND_QUEUE_PATH = LOCAL_CACHE_DIR / "outbound_queue.jsonl"
SCENARIO_STATE_PATH = LOCAL_CACHE_DIR / "scenario_state.json"
ANCHOR_API_BASE = os.environ.get("ANCHOR_API_BASE", "http://127.0.0.1:8000")
MARLIN_API_HOST = os.environ.get("MARLIN_API_HOST", "127.0.0.1")
MARLIN_API_PORT = int(os.environ.get("MARLIN_API_PORT", "9001"))

DEFAULT_LOW_BATTERY_THRESHOLD = 20
