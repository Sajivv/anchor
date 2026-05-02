from datetime import datetime, UTC


def read_gps() -> dict[str, float | str]:
    return {
        "lat": 38.9445,
        "lon": -76.4367,
        "fix_timestamp": datetime.now(UTC).isoformat(),
    }
