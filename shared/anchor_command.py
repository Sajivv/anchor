from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from typing import Any


VALID_COMMAND_TYPES = {
    "update_mission_config",
    "request_snapshot",
    "set_mode",
    "sleep_until",
    "run_wifi_scan",
    "start_wifi_monitor",
    "stop_wifi_activity",
    "ping",
}

VALID_MODES = {"passive", "active", "low_power"}


@dataclass
class AnchorCommand:
    command_id: str
    node_id: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)
    issued_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def validate(self) -> None:
        if self.type not in VALID_COMMAND_TYPES:
            raise ValueError(f"Unsupported command type: {self.type}")
        if self.type == "set_mode":
            mode = self.params.get("mode")
            if mode not in VALID_MODES:
                raise ValueError(f"Unsupported mode: {mode}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
