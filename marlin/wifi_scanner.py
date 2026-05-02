from datetime import datetime, UTC
from typing import Any

from marlin.scenario_state import load_state


def scan_wifi() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    meta = {
        "scan_performed": True,
        "scan_timestamp": datetime.now(UTC).isoformat(),
    }
    state = load_state()
    override = state.get("wifi_override")
    if override is not None:
        return meta, override
    networks = [
        {
            "ssid": "TestNet-1",
            "bssid": "AA:BB:CC:DD:EE:FF",
            "rssi": -67,
            "channel": 6,
        }
    ]
    return meta, networks
