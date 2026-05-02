from shared.anchor_command import AnchorCommand

from marlin.local_store import load_json, save_json
from marlin.config import MISSION_CONFIG_PATH, NODE_STATE_PATH
from marlin.snapshot_builder import build_snapshot
from marlin import gps_reader, battery_reader, temp_humidity_reader, wifi_scanner
from marlin.scenario_state import consume_fail_next_command
from marlin.wifi_task_runner import run_wifi_scan, start_wifi_monitor, stop_wifi_activity


def execute_command(command: AnchorCommand) -> tuple[str, dict]:
    if consume_fail_next_command():
        raise RuntimeError("Scenario injected command failure")

    if command.type == "ping":
        return "Ping received", {"alive": True}

    if command.type == "request_snapshot":
        snapshot = _build_live_snapshot(command.node_id)
        return "Snapshot generated", {"snapshot": snapshot.to_dict()}

    if command.type == "run_wifi_scan":
        result = run_wifi_scan(command.params.get("duration_sec", 60))
        return "Wi-Fi scan finished", result

    if command.type == "start_wifi_monitor":
        result = start_wifi_monitor(
            command.params.get("target", {}),
            command.params.get("duration_sec", 300),
        )
        return "Wi-Fi monitor started", result

    if command.type == "stop_wifi_activity":
        result = stop_wifi_activity()
        return "Wi-Fi activity stopped", result

    if command.type == "set_mode":
        node_state = load_json(NODE_STATE_PATH, default={})
        node_state["mode"] = command.params["mode"]
        save_json(NODE_STATE_PATH, node_state)
        return "Mode updated", {"mode": command.params["mode"]}

    if command.type == "update_mission_config":
        mission_config = load_json(MISSION_CONFIG_PATH, default={})
        patch = command.params.get("patch", {})
        merged = _deep_merge(mission_config, patch)
        save_json(MISSION_CONFIG_PATH, merged)
        return "Mission config updated", {"updated_keys": sorted(patch.keys())}

    if command.type == "sleep_until":
        return "Sleep condition stored", command.params

    raise ValueError(f"Unsupported command type: {command.type}")


def _build_live_snapshot(node_id: str):
    gps = gps_reader.read_gps()
    battery = battery_reader.read_battery()
    environment = temp_humidity_reader.read_temperature_humidity()
    wifi_scan_meta, wifi_scan = wifi_scanner.scan_wifi()
    node_state = load_json(NODE_STATE_PATH, default={})
    mode = node_state.get("mode", "active")
    return build_snapshot(
        node_id=node_id,
        mode=mode,
        gps=gps,
        battery=battery,
        environment=environment,
        wifi_scan_meta=wifi_scan_meta,
        wifi_scan=wifi_scan,
    )


def _deep_merge(base: dict, patch: dict) -> dict:
    result = dict(base)
    for key, value in patch.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
