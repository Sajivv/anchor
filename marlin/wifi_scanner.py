from datetime import datetime, UTC
from typing import Any


def scan_wifi() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    meta = {
        "scan_performed": True,
        "scan_timestamp": datetime.now(UTC).isoformat(),
    }
    networks = [
        {
            "ssid": "TestNet-1",
            "bssid": "AA:BB:CC:DD:EE:FF",
            "rssi": -67,
            "channel": 6,
        }
    ]
    return meta, networks
