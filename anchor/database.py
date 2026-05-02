import json
from pathlib import Path
from typing import Any


def load_database(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _normalize_database(
            {
                "missions": {},
                "fleet_state": {},
                "messages": [],
                "reasoning_runs": [],
                "commands": [],
                "chat_history": [],
            }
        )
    return _normalize_database(json.loads(path.read_text(encoding="utf-8")))


def _normalize_database(data: dict[str, Any]) -> dict[str, Any]:
    defaults = {
        "missions": {},
        "fleet_state": {},
        "messages": [],
        "reasoning_runs": [],
        "commands": [],
        "chat_history": [],
    }
    for key, value in defaults.items():
        data.setdefault(key, value)
    return data


def save_database(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def append_message(db: dict[str, Any], message: dict[str, Any]) -> None:
    db["messages"].append(message)


def append_chat_message(db: dict[str, Any], role: str, text: str) -> None:
    db["chat_history"].append({"role": role, "text": text})
