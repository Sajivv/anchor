from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Snapshot:
    node_id: str
    timestamp: str
    mode: str
    gps: dict[str, float]
    battery: dict[str, float | int]
    environment: dict[str, float] = field(default_factory=dict)
    wifi_scan_meta: dict[str, Any] = field(default_factory=dict)
    wifi_scan: list[dict[str, Any]] = field(default_factory=list)
    message_type: str = "snapshot"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
