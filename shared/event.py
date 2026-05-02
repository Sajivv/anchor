from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from typing import Any


VALID_EVENT_TYPES = {
    "entered_geofence",
    "left_geofence",
    "mode_changed",
    "low_battery",
    "target_detected",
    "command_failed",
}


@dataclass
class Event:
    event_id: str
    node_id: str
    type: str
    severity: str = "info"
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    message_type: str = "event"

    def validate(self) -> None:
        if self.type not in VALID_EVENT_TYPES:
            raise ValueError(f"Unsupported event type: {self.type}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
