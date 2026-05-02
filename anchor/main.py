import argparse

from anchor.api_server import create_server, receive_message
from anchor.command_center import make_command, record_command
from anchor.config import DATABASE_PATH
from anchor.database import append_message, load_database, save_database
from anchor.fleet_manager import update_fleet_state
from anchor.map_tracker import build_map_marker
from anchor.mission_manager import get_mission_config
from anchor.policy_guard import evaluate_action
from anchor.reasoning_engine import build_reasoning_context, reason, should_trigger_reasoning
from marlin.main import default_mission_config


def sample_event(node_id: str, event_id: str, timestamp: str) -> dict:
    return {
        "message_type": "event",
        "event_id": event_id,
        "node_id": node_id,
        "type": "entered_geofence",
        "severity": "info",
        "timestamp": timestamp,
        "details": {"geofence_id": "target-zone-1"},
    }


def sample_snapshot(
    node_id: str,
    lat: float,
    lon: float,
    battery_percent: int,
    mode: str,
    timestamp: str,
    scan_timestamp: str,
) -> dict:
    return {
        "message_type": "snapshot",
        "node_id": node_id,
        "timestamp": timestamp,
        "mode": mode,
        "gps": {"lat": lat, "lon": lon},
        "battery": {"percent": battery_percent},
        "environment": {"temperature_c": 21.4, "humidity_pct": 68.2},
        "wifi_scan_meta": {
            "scan_performed": True,
            "scan_timestamp": scan_timestamp,
        },
        "wifi_scan": [
            {
                "ssid": "TestNet-1",
                "bssid": "AA:BB:CC:DD:EE:FF",
                "rssi": -67,
                "channel": 6,
            }
        ],
    }


def process_message(db: dict, message: dict) -> dict:
    db = load_database(DATABASE_PATH)
    receipt = receive_message(message)
    append_message(db, message)
    update_fleet_state(db, message)

    if should_trigger_reasoning(message):
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
                print(f"Approved command: {command.to_dict()}")
            else:
                print(f"Rejected action: {decision}")

    save_database(DATABASE_PATH, db)
    return {
        "receipt": receipt,
        "marker": build_map_marker(db["fleet_state"].get(message["node_id"], {})),
    }


def build_demo_missions() -> list[dict]:
    base = default_mission_config().to_dict()
    north = {
        **base,
        "mission_id": "mission-002",
        "node_id": "marlin-02",
        "active_geofence": {
            **base["active_geofence"],
            "center_lat": 38.9850,
            "center_lon": -76.4367,
        },
    }
    south = {
        **base,
        "mission_id": "mission-003",
        "node_id": "marlin-03",
        "active_geofence": {
            **base["active_geofence"],
            "center_lat": 38.8865,
            "center_lon": -76.4367,
        },
    }
    return [base, north, south]


def build_demo_snapshots() -> list[dict]:
    return [
        sample_snapshot(
            node_id="marlin-01",
            lat=38.9445,
            lon=-76.4367,
            battery_percent=82,
            mode="active",
            timestamp="2026-05-01T12:00:30Z",
            scan_timestamp="2026-05-01T12:00:20Z",
        ),
        sample_snapshot(
            node_id="marlin-02",
            lat=38.9850,
            lon=-76.4367,
            battery_percent=79,
            mode="active",
            timestamp="2026-05-01T12:01:00Z",
            scan_timestamp="2026-05-01T12:00:48Z",
        ),
        sample_snapshot(
            node_id="marlin-03",
            lat=38.8865,
            lon=-76.4367,
            battery_percent=76,
            mode="passive",
            timestamp="2026-05-01T12:01:30Z",
            scan_timestamp="2026-05-01T12:01:18Z",
        ),
    ]


def build_demo_events() -> list[dict]:
    return [
        sample_event("marlin-01", "evt-001", "2026-05-01T12:00:00Z"),
        sample_event("marlin-02", "evt-002", "2026-05-01T12:00:40Z"),
        sample_event("marlin-03", "evt-003", "2026-05-01T12:01:10Z"),
    ]


def seed_demo_data(reset: bool = False) -> dict:
    if reset:
        save_database(
            DATABASE_PATH,
            {
                "missions": {},
                "fleet_state": {},
                "messages": [],
                "reasoning_runs": [],
                "commands": [],
                "chat_history": [],
            },
        )
    db = load_database(DATABASE_PATH)
    if not db["chat_history"]:
        db["chat_history"] = [
            {
                "role": "anchor",
                "text": "ANCHOR online. I can help define deployment status, geofence objectives, scan behavior, and reporting policy for each MARLIN.",
            },
            {
                "role": "anchor",
                "text": "Start by telling me whether the MARLINs are already deployed or about to be deployed.",
            },
        ]
    for mission in build_demo_missions():
        db["missions"][mission["node_id"]] = mission
    save_database(DATABASE_PATH, db)
    for snapshot in build_demo_snapshots():
        process_message(db, snapshot)
    for event in build_demo_events():
        process_message(db, event)
    return {
        "status": "seeded",
        "nodes_seeded": 3,
    }


def run_once() -> None:
    result = process_message(
        load_database(DATABASE_PATH),
        sample_event("marlin-01", "evt-001", "2026-05-01T12:00:00Z"),
    )
    print(f"Message receipt: {result['receipt']}")
    print(f"Current marker: {result['marker']}")


def serve(host: str, port: int) -> None:
    server = create_server(host, port, seed_demo_data)
    print(f"ANCHOR dashboard running at http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ANCHOR prototype")
    parser.add_argument("--serve", action="store_true", help="Start the web UI server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--seed-demo", action="store_true", help="Load demo data first")
    args = parser.parse_args()

    if args.seed_demo:
        result = seed_demo_data()
        print(f"Seeded demo data: {result['status']}")
    if args.serve:
        serve(args.host, args.port)
        return
    run_once()


if __name__ == "__main__":
    main()
