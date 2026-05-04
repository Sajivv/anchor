from pathlib import Path

from marlin.config import MARLIN_BATTERY_PATH, MARLIN_BATTERY_SOURCE
from marlin.scenario_state import load_state


DEFAULT_BATTERY_PERCENT = 82


def _capacity_path_candidates() -> list[Path]:
    if MARLIN_BATTERY_PATH:
        return [Path(MARLIN_BATTERY_PATH)]

    power_supply_dir = Path("/sys/class/power_supply")
    if not power_supply_dir.exists():
        return []

    candidates: list[Path] = []
    for battery_dir in sorted(power_supply_dir.glob("BAT*")):
        capacity_path = battery_dir / "capacity"
        if capacity_path.exists():
            candidates.append(capacity_path)
    return candidates


def _read_system_battery_percent() -> int | None:
    for capacity_path in _capacity_path_candidates():
        try:
            raw_value = capacity_path.read_text(encoding="utf-8").strip()
            return max(0, min(100, int(raw_value)))
        except (OSError, ValueError):
            continue
    return None


def read_battery() -> dict[str, int]:
    state = load_state()
    override = state.get("battery_override")
    if override is not None:
        return {"percent": int(override)}

    if MARLIN_BATTERY_SOURCE == "system":
        system_percent = _read_system_battery_percent()
        if system_percent is not None:
            return {"percent": system_percent}

    return {"percent": DEFAULT_BATTERY_PERCENT}
