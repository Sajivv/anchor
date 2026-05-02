import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from shared.anchor_command import AnchorCommand

from marlin.command_handler import accept_command, complete_command, fail_command
from marlin.config import ANCHOR_API_BASE
from marlin.executor import execute_command
from marlin.uploader import queue_message, deliver_queued_messages
from marlin.config import OUTBOUND_QUEUE_PATH


def create_server(host: str, port: int) -> ThreadingHTTPServer:
    class MarlinHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            if self.path == "/api/commands":
                self._handle_command()
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

        def _respond_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return ThreadingHTTPServer((host, port), MarlinHandler)
