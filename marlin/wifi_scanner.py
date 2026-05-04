from datetime import UTC, datetime
import csv
import io
import shutil
import subprocess
from typing import Any

from marlin.config import (
    MARLIN_WIFI_INTERFACE,
    MARLIN_WIFI_SCAN_TIMEOUT_SEC,
    MARLIN_WIFI_SOURCE,
)
from marlin.scenario_state import load_state


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _mock_networks() -> list[dict[str, Any]]:
    return [
        {
            "ssid": "TestNet-1",
            "bssid": "AA:BB:CC:DD:EE:FF",
            "rssi": -67,
            "channel": 6,
        }
    ]


def _coerce_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _detect_wifi_interface() -> str | None:
    if MARLIN_WIFI_INTERFACE:
        return MARLIN_WIFI_INTERFACE

    if shutil.which("nmcli") is None:
        return None

    result = subprocess.run(
        ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device", "status"],
        check=False,
        capture_output=True,
        text=True,
        timeout=MARLIN_WIFI_SCAN_TIMEOUT_SEC,
    )
    if result.returncode != 0:
        return None

    wifi_candidates: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split(":")
        if len(parts) < 3:
            continue
        device, dev_type, state = parts[0], parts[1], parts[2]
        if dev_type == "wifi":
            wifi_candidates.append((device, state))

    for device, state in wifi_candidates:
        if state in {"connected", "connecting", "disconnected"}:
            return device

    return wifi_candidates[0][0] if wifi_candidates else None


def _scan_with_nmcli() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    interface = _detect_wifi_interface()
    if interface is None:
        raise RuntimeError("No Wi-Fi interface found for nmcli scan")

    cmd = [
        "nmcli",
        "--terse",
        "--escape",
        "no",
        "--fields",
        "SSID,BSSID,SIGNAL,CHAN",
        "device",
        "wifi",
        "list",
        "ifname",
        interface,
        "--rescan",
        "yes",
    ]
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=MARLIN_WIFI_SCAN_TIMEOUT_SEC,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "nmcli scan failed")

    networks: list[dict[str, Any]] = []
    reader = csv.reader(io.StringIO(result.stdout), delimiter=":")
    for row in reader:
        if len(row) < 4:
            continue
        ssid, bssid, signal, channel = row[0], row[1], row[2], row[3]
        if not bssid:
            continue
        networks.append(
            {
                "ssid": ssid or "<hidden>",
                "bssid": bssid,
                "rssi": _coerce_int(signal),
                "channel": _coerce_int(channel),
            }
        )

    meta = {
        "scan_performed": True,
        "scan_timestamp": _now(),
        "scan_backend": "nmcli",
        "interface": interface,
        "network_count": len(networks),
    }
    return meta, networks


def scan_wifi() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    state = load_state()
    override = state.get("wifi_override")
    if override is not None:
        return {
            "scan_performed": True,
            "scan_timestamp": _now(),
            "scan_backend": "scenario_override",
            "network_count": len(override),
        }, override

    if MARLIN_WIFI_SOURCE == "system":
        try:
            return _scan_with_nmcli()
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            pass

    networks = _mock_networks()
    return {
        "scan_performed": True,
        "scan_timestamp": _now(),
        "scan_backend": "mock",
        "network_count": len(networks),
    }, networks
