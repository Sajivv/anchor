import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request
from urllib.parse import parse_qs, urlparse

from anchor.config import BASE_DIR, DATABASE_PATH
from anchor.database import (
    append_chat_message,
    attach_command_to_active_run,
    load_database,
    save_database,
    start_scenario_run,
)
from anchor.ingest import process_message
from anchor.command_center import make_command, send_command


WEB_INDEX_PATH = BASE_DIR / "web" / "index.html"

def _load_index_html() -> str:
    return WEB_INDEX_PATH.read_text(encoding="utf-8")


def _build_state_payload() -> dict:
    db = load_database(DATABASE_PATH)
    fleet_state = db.get("fleet_state", {})
    markers = []
    for node_id, entry in fleet_state.items():
        gps = entry.get("gps") or {}
        markers.append(
            {
                "node_id": node_id,
                "lat": gps.get("lat"),
                "lon": gps.get("lon"),
                "mode": entry.get("mode"),
                "battery": (entry.get("battery") or {}).get("percent"),
                "last_snapshot_at": entry.get("last_snapshot_at"),
                "last_event_type": entry.get("last_event_type"),
            }
        )
    return {"database": db, "markers": markers, "system_mode": db.get("system_mode", "anchor_managed")}


def _anchor_chat_reply(user_text: str, db: dict) -> str:
    lower = user_text.lower()
    fleet_size = len(db.get("fleet_state", {}))
    if "deploy" in lower:
        return (
            "Understood. I would turn that into mission setup questions: deployment "
            "status, target geofence, passive reporting interval, and when active "
            "Wi-Fi scanning should begin."
        )
    if "geofence" in lower:
        return (
            "I can treat a single active geofence as the version 1 mission boundary "
            "and push it to each MARLIN as long-lived policy."
        )
    if "scan" in lower or "wifi" in lower:
        return (
            "For version 1, I would keep Wi-Fi behavior mission-driven: passive while "
            "drifting, active scanning after geofence entry, and targeted monitoring "
            "through structured commands."
        )
    if "marlin" in lower or "fleet" in lower:
        return (
            f"I currently see {fleet_size} tracked MARLIN node"
            f"{'' if fleet_size == 1 else 's'} in ANCHOR. I can help inspect node "
            "state, mission config, or command behavior."
        )
    return (
        "I can help translate that into mission config fields, ANCHOR commands, "
        "or MARLIN behavior. Ask me about deployment, geofence rules, reporting "
        "cadence, or Wi-Fi activity."
    )


def create_server(host: str, port: int, seed_callback) -> ThreadingHTTPServer:
    class AnchorHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._respond_html(_load_index_html())
                return
            if parsed.path == "/api/state":
                self._respond_json(_build_state_payload())
                return
            if parsed.path == "/api/demo/seed":
                query = parse_qs(parsed.query)
                reset = query.get("reset", ["0"])[0] == "1"
                result = seed_callback(reset=reset)
                self._respond_json(result)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/chat":
                self._handle_chat()
                return
            if parsed.path == "/api/messages":
                self._handle_message()
                return
            if parsed.path == "/api/dispatch-command":
                self._handle_dispatch_command()
                return
            if parsed.path == "/api/system-mode":
                self._handle_system_mode()
                return
            if parsed.path == "/api/inject-scenario":
                self._handle_inject_scenario()
                return
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

        def log_message(self, format: str, *args) -> None:
            return

        def _handle_chat(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw_body.decode("utf-8"))
            user_text = str(payload.get("text", "")).strip()
            if not user_text:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing chat text")
                return

            db = load_database(DATABASE_PATH)
            append_chat_message(db, "user", user_text)
            reply = _anchor_chat_reply(user_text, db)
            append_chat_message(db, "anchor", reply)
            save_database(DATABASE_PATH, db)
            self._respond_json({"reply": reply, "chat_history": db["chat_history"]})

        def _handle_message(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw_body.decode("utf-8"))
            message_type = payload.get("message_type")
            if message_type not in {"snapshot", "event", "command_response"}:
                self.send_error(HTTPStatus.BAD_REQUEST, "Unsupported message_type")
                return
            result = process_message(payload)
            self._respond_json(result)

        def _handle_dispatch_command(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw_body.decode("utf-8"))
            node_id = str(payload.get("node_id", "")).strip()
            command_type = str(payload.get("command_type", "")).strip()
            params = payload.get("params", {})
            if not node_id or not command_type:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing node_id or command_type")
                return

            db = load_database(DATABASE_PATH)
            command_id = f"manual-{len(db.get('commands', [])) + 1:03d}"
            command = make_command(command_id, node_id, command_type, params)
            db["commands"].append(command.to_dict())
            attach_command_to_active_run(db, node_id, command.to_dict())
            save_database(DATABASE_PATH, db)
            delivery_result = send_command(command)
            db = load_database(DATABASE_PATH)
            if db["commands"]:
                db["commands"][-1]["delivery_result"] = delivery_result
                save_database(DATABASE_PATH, db)
            self._respond_json(
                {
                    "status": "sent",
                    "command": command.to_dict(),
                    "delivery_result": delivery_result,
                }
            )

        def _handle_system_mode(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw_body.decode("utf-8"))
            mode = str(payload.get("mode", "")).strip()
            if mode not in {"baseline", "anchor_managed"}:
                self.send_error(HTTPStatus.BAD_REQUEST, "Unsupported mode")
                return
            db = load_database(DATABASE_PATH)
            db["system_mode"] = mode
            save_database(DATABASE_PATH, db)
            self._respond_json({"status": "updated", "system_mode": mode})

        def _handle_inject_scenario(self) -> None:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length) if content_length else b"{}"
            payload = json.loads(raw_body.decode("utf-8"))
            node_id = str(payload.get("node_id", "")).strip()
            scenario = str(payload.get("scenario", "")).strip()
            if not node_id or not scenario:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing node_id or scenario")
                return

            db = load_database(DATABASE_PATH)
            run = start_scenario_run(db, node_id, scenario)
            save_database(DATABASE_PATH, db)

            req = request.Request(
                url="http://127.0.0.1:9001/api/scenario",
                data=json.dumps(
                    {
                        "node_id": node_id,
                        "scenario": scenario,
                        "trigger_cycle": True,
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
            self._respond_json({"status": "sent", "run": run, "result": result})

        def _respond_html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _respond_json(self, payload: dict) -> None:
            encoded = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return ThreadingHTTPServer((host, port), AnchorHandler)
