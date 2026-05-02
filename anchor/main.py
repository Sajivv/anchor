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


def sample_event() -> dict:
    return {
        "message_type": "event",
        "event_id": "evt-001",
        "node_id": "marlin-01",
        "type": "entered_geofence",
        "severity": "info",
        "timestamp": "2026-05-01T12:00:00Z",
        "details": {"geofence_id": "target-zone-1"},
    }


def sample_snapshot() -> dict:
    return {
        "message_type": "snapshot",
        "node_id": "marlin-01",
        "timestamp": "2026-05-01T12:00:30Z",
        "mode": "active",
        "gps": {"lat": 36.8501, "lon": -76.2859},
        "battery": {"percent": 82},
        "environment": {"temperature_c": 21.4, "humidity_pct": 68.2},
        "wifi_scan_meta": {
            "scan_performed": True,
            "scan_timestamp": "2026-05-01T12:00:20Z",
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
            },
        )
    db = load_database(DATABASE_PATH)
    mission = default_mission_config().to_dict()
    db["missions"][mission["node_id"]] = mission
    save_database(DATABASE_PATH, db)
    snapshot_result = process_message(db, sample_snapshot())
    event_result = process_message(db, sample_event())
    return {
        "status": "seeded",
        "snapshot_result": snapshot_result,
        "event_result": event_result,
    }


def run_once() -> None:
    result = process_message(load_database(DATABASE_PATH), sample_event())
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
