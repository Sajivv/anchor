from marlin.scenario_state import load_state


def read_battery() -> dict[str, int]:
    state = load_state()
    override = state.get("battery_override")
    if override is not None:
        return {"percent": int(override)}
    return {"percent": 82}
