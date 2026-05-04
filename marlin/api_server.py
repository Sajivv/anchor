import json
import time
from datetime import datetime, UTC
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from shared.anchor_command import AnchorCommand
from shared.event import Event

from marlin.command_handler import accept_command, complete_command, fail_command
from marlin.config import ANCHOR_API_BASE
from marlin.executor import execute_command
from marlin.uploader import queue_message, deliver_queued_messages
from marlin.config import OUTBOUND_QUEUE_PATH
from marlin.scenario_state import reset_state, update_state


def create_server(host: str, port: int) -> ThreadingHTTPServer:
    class MarlinHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path == "/api/commands":
                self._handle_command()
                return
            if self.path == "/api/scenario":
                self._handle_scenario()
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def log_message(self, format: str, *args) -> None:
            return

        def _handle_command(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw_body.decode("utf-8"))

            try:
                command = AnchorCommand(**payload)
                accepted = accept_command(command)
                queue_message(OUTBOUND_QUEUE_PATH, accepted.to_dict())
                deliver_queued_messages(OUTBOUND_QUEUE_PATH, ANCHOR_API_BASE)

                message, result = execute_command(command)
                completed = complete_command(command, message, result)
                queue_message(OUTBOUND_QUEUE_PATH, completed.to_dict())
                deliver_queued_messages(OUTBOUND_QUEUE_PATH, ANCHOR_API_BASE)

                self._respond_json(
                    {
                        "accepted": accepted.to_dict(),
                        "completed": completed.to_dict(),
                    }
                )
            except Exception as exc:
                node_id = payload.get("node_id", "unknown")
                command_id = payload.get("command_id", "unknown")
                failed = fail_command(command_id, node_id, str(exc))
                queue_message(OUTBOUND_QUEUE_PATH, failed.to_dict())
                deliver_queued_messages(OUTBOUND_QUEUE_PATH, ANCHOR_API_BASE)
                self._respond_json({"failed": failed.to_dict()}, status=HTTPStatus.BAD_REQUEST)

        def _handle_scenario(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw_body.decode("utf-8"))
            scenario = str(payload.get("scenario", "")).strip()
            node_id = str(payload.get("node_id", "marlin-01")).strip()
            trigger_cycle = bool(payload.get("trigger_cycle", True))
            result = apply_scenario(scenario, node_id, trigger_cycle)
            self._respond_json(result)

        def _respond_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return ThreadingHTTPServer((host, port), MarlinHandler)


def apply_scenario(scenario: str, node_id: str, trigger_cycle: bool = True) -> dict:
    if scenario == "reset":
        state = reset_state()
        if trigger_cycle:
            _run_cycle()
        return {"status": "applied", "scenario": scenario, "state": state}

    if scenario == "geofence_entry":
        state = update_state(
            {
                "gps_override": None,
                "gps_path": [
                    {"lat": 38.9376, "lon": -76.4367},
                    {"lat": 38.9378, "lon": -76.4367},
                ],
            }
        )
        if trigger_cycle:
            _run_cycle()
            time.sleep(0.4)
            _emit_event(node_id, "entered_geofence", {"geofence_id": "target-zone-1"})
            _run_cycle()
        return {
            "status": "applied",
            "scenario": scenario,
            "state": state,
            "path_points": 2,
        }

    if scenario == "low_battery":
        state = update_state({"battery_override": 14})
        _emit_event(node_id, "low_battery", {"battery_percent": 14})
        if trigger_cycle:
            _run_cycle()
        return {"status": "applied", "scenario": scenario, "state": state}

    if scenario == "target_wifi_detection":
        state = update_state(
            {
                "wifi_override": [
                    {
                        "ssid": "TargetNet-Detected",
                        "bssid": "DE:AD:BE:EF:00:01",
                        "rssi": -52,
                        "channel": 11,
                    }
                ]
            }
        )
        _emit_event(
            node_id,
            "target_detected",
            {"ssid": "TargetNet-Detected", "bssid": "DE:AD:BE:EF:00:01"},
        )
        if trigger_cycle:
            _run_cycle()
        return {"status": "applied", "scenario": scenario, "state": state}

    if scenario == "disconnect":
        state = update_state({"disconnect": True})
        if trigger_cycle:
            _run_cycle()
        return {"status": "applied", "scenario": scenario, "state": state}

    if scenario == "reconnect":
        state = update_state({"disconnect": False})
        if trigger_cycle:
            _run_cycle()
        return {"status": "applied", "scenario": scenario, "state": state}

    if scenario == "command_failure":
        state = update_state({"fail_next_command": True})
        return {"status": "applied", "scenario": scenario, "state": state}

    raise ValueError(f"Unsupported scenario: {scenario}")


def _emit_event(node_id: str, event_type: str, details: dict) -> None:
    event = Event(
        event_id=f"evt-{event_type}-{datetime.now(UTC).strftime('%H%M%S')}",
        node_id=node_id,
        type=event_type,
        details=details,
    )
    queue_message(OUTBOUND_QUEUE_PATH, event.to_dict())
    deliver_queued_messages(OUTBOUND_QUEUE_PATH, ANCHOR_API_BASE)


def _run_cycle() -> None:
    from marlin.main import run_cycle

    run_cycle()
