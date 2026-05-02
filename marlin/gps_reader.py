from datetime import datetime, UTC

from marlin.scenario_state import load_state


def read_gps() -> dict[str, float | str]:
    state = load_state()
    override = state.get("gps_override")
    if override:
        return {
            "lat": override["lat"],
            "lon": override["lon"],
            "fix_timestamp": datetime.now(UTC).isoformat(),
        }
    return {
        "lat": 38.9445,
        "lon": -76.4367,
        "fix_timestamp": datetime.now(UTC).isoformat(),
    }
