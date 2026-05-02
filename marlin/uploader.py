import json
from pathlib import Path
from urllib import error, request

from marlin.scenario_state import load_state


def queue_message(path: Path, message: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(message) + "\n")


def flush_queue(path: Path) -> list[dict]:
    if not path.exists():
        return []
    messages = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                messages.append(json.loads(line))
    path.write_text("", encoding="utf-8")
    return messages


def send_message(api_base: str, message: dict) -> dict:
    state = load_state()
    if state.get("disconnect"):
        raise error.URLError("Scenario disconnect is active")
    body = json.dumps(message).encode("utf-8")
    req = request.Request(
        url=f"{api_base.rstrip('/')}/api/messages",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def deliver_queued_messages(path: Path, api_base: str) -> dict[str, int]:
    messages = flush_queue(path)
    if not messages:
        return {"sent": 0, "queued": 0}

    sent = 0
    failed_messages = []
    for message in messages:
        try:
            send_message(api_base, message)
            sent += 1
        except (OSError, error.URLError, error.HTTPError, TimeoutError):
            failed_messages.append(message)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for message in failed_messages:
            handle.write(json.dumps(message) + "\n")

    return {"sent": sent, "queued": len(failed_messages)}
