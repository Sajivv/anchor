from datetime import datetime, UTC


def read_gps() -> dict[str, float | str]:
    return {
        "lat": 36.8501,
        "lon": -76.2859,
        "fix_timestamp": datetime.now(UTC).isoformat(),
    }
