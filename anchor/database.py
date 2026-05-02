import json
from datetime import datetime, UTC
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
                "system_mode": "anchor_managed",
                "scenario_runs": [],
                "active_runs": {},
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
        "system_mode": "anchor_managed",
        "scenario_runs": [],
        "active_runs": {},
    }
    for key, value in defaults.items():
        data.setdefault(key, value)
    return data


def save_database(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_normalize_database(data), indent=2), encoding="utf-8")


def append_message(db: dict[str, Any], message: dict[str, Any]) -> None:
    db["messages"].append(message)


def append_chat_message(db: dict[str, Any], role: str, text: str) -> None:
    db["chat_history"].append({"role": role, "text": text})


def start_scenario_run(db: dict[str, Any], node_id: str, scenario: str) -> dict[str, Any]:
    finalize_active_run(db, node_id, status="superseded")
    run = {
        "run_id": f"run-{len(db['scenario_runs']) + 1:03d}",
        "node_id": node_id,
        "scenario": scenario,
        "system_mode": db.get("system_mode", "anchor_managed"),
        "started_at": datetime.now(UTC).isoformat(),
        "ended_at": None,
        "status": "running",
        "events": [],
        "snapshots": [],
        "command_responses": [],
        "commands": [],
        "notes": [],
    }
    db["scenario_runs"].append(run)
    db["active_runs"][node_id] = run["run_id"]
    return run


def finalize_active_run(db: dict[str, Any], node_id: str, status: str = "completed") -> None:
    run_id = db.get("active_runs", {}).pop(node_id, None)
    if not run_id:
        return
    run = get_run(db, run_id)
    if not run or run["ended_at"] is not None:
        return
    run["ended_at"] = datetime.now(UTC).isoformat()
    run["status"] = status


def get_run(db: dict[str, Any], run_id: str) -> dict[str, Any] | None:
    for run in db["scenario_runs"]:
        if run["run_id"] == run_id:
            return run
    return None


def attach_message_to_active_run(db: dict[str, Any], message: dict[str, Any]) -> None:
    node_id = message.get("node_id")
    if not node_id:
        return
    run_id = db.get("active_runs", {}).get(node_id)
    if not run_id:
        return
    run = get_run(db, run_id)
    if not run:
        return

    message_type = message.get("message_type")
    summary = {
        "timestamp": message.get("timestamp"),
        "message_type": message_type,
    }
    if message_type == "event":
        summary["type"] = message.get("type")
        run["events"].append(summary)
    elif message_type == "snapshot":
        summary["mode"] = message.get("mode")
        summary["battery"] = (message.get("battery") or {}).get("percent")
        run["snapshots"].append(summary)
    elif message_type == "command_response":
        summary["command_id"] = message.get("command_id")
        summary["status"] = message.get("status")
        run["command_responses"].append(summary)


def attach_command_to_active_run(db: dict[str, Any], node_id: str, command: dict[str, Any]) -> None:
    run_id = db.get("active_runs", {}).get(node_id)
    if not run_id:
        return
    run = get_run(db, run_id)
    if not run:
        return
    run["commands"].append(
        {
            "command_id": command.get("command_id"),
            "type": command.get("type"),
            "issued_at": command.get("issued_at"),
        }
    )
