import json
from pathlib import Path
from typing import Any


def load_database(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "missions": {},
            "fleet_state": {},
            "messages": [],
            "reasoning_runs": [],
            "commands": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_database(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def append_message(db: dict[str, Any], message: dict[str, Any]) -> None:
    db["messages"].append(message)
