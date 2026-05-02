def update_fleet_state(db: dict, message: dict) -> None:
    node_id = message.get("node_id", "unknown")
    fleet_entry = db["fleet_state"].setdefault(node_id, {})
    message_type = message.get("message_type")

    if message_type == "snapshot":
        fleet_entry.update(
            {
                "last_snapshot_at": message.get("timestamp"),
                "mode": message.get("mode"),
                "gps": message.get("gps"),
                "battery": message.get("battery"),
                "environment": message.get("environment", {}),
                "wifi_scan_meta": message.get("wifi_scan_meta", {}),
            }
        )
    elif message_type == "event":
        fleet_entry["last_event_at"] = message.get("timestamp")
        fleet_entry["last_event_type"] = message.get("type")
    elif message_type == "command_response":
        fleet_entry["last_command_response_at"] = message.get("timestamp")
        fleet_entry["last_command_status"] = message.get("status")
