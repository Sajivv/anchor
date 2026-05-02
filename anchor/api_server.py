import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from anchor.config import BASE_DIR, DATABASE_PATH
from anchor.database import load_database


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

        def log_message(self, format: str, *args) -> None:
            return

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
