from urllib.error import HTTPError, URLError

from anchor.command_center import make_command, record_command, send_command
from anchor.config import DATABASE_PATH
from anchor.database import (
    append_message,
    attach_command_to_active_run,
    attach_message_to_active_run,
    load_database,
    maybe_finalize_active_run,
    save_database,
)
from anchor.fleet_manager import update_fleet_state
from anchor.map_tracker import build_map_marker
from anchor.mission_manager import get_mission_config
from anchor.policy_guard import evaluate_action
from anchor.reasoning_engine import build_reasoning_context, reason, should_trigger_reasoning


def process_message(message: dict) -> dict:
    db = load_database(DATABASE_PATH)
    append_message(db, message)
    update_fleet_state(db, message)
    attach_message_to_active_run(db, message)

    if db.get("system_mode", "anchor_managed") == "anchor_managed" and should_trigger_reasoning(message):
        fleet_entry = db["fleet_state"].get(message["node_id"], {})
        mission_config = get_mission_config(db, message["node_id"])
        context = build_reasoning_context(message, fleet_entry, mission_config)
        reasoning_result = reason(context)
        db["reasoning_runs"].append(reasoning_result)

        for index, action in enumerate(reasoning_result["recommended_actions"], start=1):
            approved, decision = evaluate_action(action, reasoning_result["confidence"])
            if approved:
                command = make_command(
                    command_id=f"cmd-{index:03d}",
                    node_id=message["node_id"],
                    command_type=action["type"],
                    params=action.get("params", {}),
                )
                record_command(db, command)
                attach_command_to_active_run(db, message["node_id"], command.to_dict())
                save_database(DATABASE_PATH, db)
                try:
                    command_result = send_command(command)
                    db = load_database(DATABASE_PATH)
                    for existing_command in db["commands"]:
                        if existing_command.get("command_id") == command.command_id:
                            existing_command["delivery_result"] = command_result
                            break
                except (OSError, HTTPError, URLError, TimeoutError) as exc:
                    db = load_database(DATABASE_PATH)
                    for existing_command in db["commands"]:
                        if existing_command.get("command_id") == command.command_id:
                            existing_command["delivery_error"] = str(exc)
                            break
                print(f"Approved command: {command.to_dict()}")
            else:
                print(f"Rejected action: {decision}")

    maybe_finalize_active_run(db, message["node_id"])

    save_database(DATABASE_PATH, db)
    return {
        "status": "received",
        "message_type": message.get("message_type"),
        "node_id": message.get("node_id"),
        "system_mode": db.get("system_mode", "anchor_managed"),
        "marker": build_map_marker(db["fleet_state"].get(message["node_id"], {})),
    }
