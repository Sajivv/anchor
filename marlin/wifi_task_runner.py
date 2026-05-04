from marlin.wifi_scanner import scan_wifi


def run_wifi_scan(duration_sec: int = 60) -> dict[str, object]:
    meta, networks = scan_wifi()
    return {
        "duration_sec": duration_sec,
        "networks_found": len(networks),
        "scan_backend": meta.get("scan_backend"),
        "interface": meta.get("interface"),
        "networks": networks,
    }


def start_wifi_monitor(target: dict, duration_sec: int) -> dict:
    return {
        "target": target,
        "duration_sec": duration_sec,
        "status": "started",
    }


def stop_wifi_activity() -> dict[str, str]:
    return {"status": "stopped"}
