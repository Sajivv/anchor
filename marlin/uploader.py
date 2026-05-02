import json
from pathlib import Path


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
