def run_wifi_scan(duration_sec: int = 60) -> dict[str, int]:
    return {"duration_sec": duration_sec, "networks_found": 1}


def start_wifi_monitor(target: dict, duration_sec: int) -> dict:
    return {
        "target": target,
        "duration_sec": duration_sec,
        "status": "started",
    }


def stop_wifi_activity() -> dict[str, str]:
    return {"status": "stopped"}
