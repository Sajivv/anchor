from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOCAL_CACHE_DIR = BASE_DIR / "marlin_cache"
MISSION_CONFIG_PATH = LOCAL_CACHE_DIR / "mission_config.json"
NODE_STATE_PATH = LOCAL_CACHE_DIR / "node_state.json"
OUTBOUND_QUEUE_PATH = LOCAL_CACHE_DIR / "outbound_queue.jsonl"

DEFAULT_LOW_BATTERY_THRESHOLD = 20
