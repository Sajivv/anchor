import json
import os
from urllib import request

from shared.anchor_command import AnchorCommand


def make_command(command_id: str, node_id: str, command_type: str, params: dict) -> AnchorCommand:
    command = AnchorCommand(
        command_id=command_id,
        node_id=node_id,
        type=command_type,
        params=params,
    )
    command.validate()
    return command


def record_command(db: dict, command: AnchorCommand) -> None:
    db["commands"].append(command.to_dict())


def send_command(command: AnchorCommand, api_base: str | None = None) -> dict:
    target_base = api_base or os.environ.get("MARLIN_API_BASE", "http://127.0.0.1:9001")
    body = json.dumps(command.to_dict()).encode("utf-8")
    req = request.Request(
        url=f"{target_base.rstrip('/')}/api/commands",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))
