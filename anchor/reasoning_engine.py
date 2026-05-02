def should_trigger_reasoning(message: dict) -> bool:
    trigger_events = {
        "entered_geofence",
        "left_geofence",
        "target_detected",
        "low_battery",
        "command_failed",
    }
    if message.get("message_type") == "event":
        return message.get("type") in trigger_events
    return False


def build_reasoning_context(
    message: dict,
    fleet_entry: dict,
    mission_config: dict | None,
) -> dict:
    return {
        "trigger": {
            "type": message.get("type", message.get("message_type")),
            "timestamp": message.get("timestamp"),
        },
        "node_summary": {
            "node_id": message.get("node_id"),
            "mode": fleet_entry.get("mode"),
            "gps": fleet_entry.get("gps"),
            "battery": fleet_entry.get("battery"),
        },
        "mission_config": mission_config,
        "recent_history": {
            "recent_events": [],
            "recent_commands": [],
            "recent_snapshots": [],
        },
        "allowed_actions": [
            "update_mission_config",
            "request_snapshot",
            "set_mode",
            "sleep_until",
            "run_wifi_scan",
            "start_wifi_monitor",
            "stop_wifi_activity",
            "ping",
        ],
    }


def reason(context: dict) -> dict:
    trigger_type = context["trigger"]["type"]
    if trigger_type == "entered_geofence":
        return {
            "summary": "Node entered the active geofence and should begin active scanning.",
            "recommended_actions": [
                {
                    "type": "run_wifi_scan",
                    "params": {"duration_sec": 60, "channels": [1, 6, 11]},
                }
            ],
            "mission_config_patch": None,
            "confidence": 0.9,
        }
    return {
        "summary": "No action needed.",
        "recommended_actions": [],
        "mission_config_patch": None,
        "confidence": 0.8,
    }
