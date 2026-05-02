from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from typing import Any


VALID_RESPONSE_STATUSES = {"accepted", "rejected", "completed", "failed"}


@dataclass
class CommandResponse:
    command_id: str
    node_id: str
    status: str
    message: str
    result: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    message_type: str = "command_response"

    def validate(self) -> None:
        if self.status not in VALID_RESPONSE_STATUSES:
            raise ValueError(f"Unsupported response status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
