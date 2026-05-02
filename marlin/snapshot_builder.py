from datetime import datetime, UTC

from shared.snapshot import Snapshot


def build_snapshot(
    node_id: str,
    mode: str,
    gps: dict,
    battery: dict,
    environment: dict,
    wifi_scan_meta: dict,
    wifi_scan: list[dict],
) -> Snapshot:
    return Snapshot(
        node_id=node_id,
        timestamp=datetime.now(UTC).isoformat(),
        mode=mode,
        gps={"lat": gps["lat"], "lon": gps["lon"]},
        battery=battery,
        environment=environment,
        wifi_scan_meta=wifi_scan_meta,
        wifi_scan=wifi_scan,
    )
