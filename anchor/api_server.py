import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from anchor.config import BASE_DIR, DATABASE_PATH
from anchor.database import append_chat_message, load_database, save_database


WEB_INDEX_PATH = BASE_DIR / "web" / "index.html"


def receive_message(message: dict) -> dict:
    return {"status": "received", "message_type": message.get("message_type")}


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
    return {"database": db, "markers": markers}


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
