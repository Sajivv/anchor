from marlin.config import SCENARIO_STATE_PATH
from marlin.local_store import load_json, save_json


def load_state() -> dict:
    return load_json(
        SCENARIO_STATE_PATH,
        default={
            "gps_override": None,
            "gps_path": None,
            "battery_override": None,
            "wifi_override": None,
            "disconnect": False,
            "fail_next_command": False,
        },
    )


def save_state(state: dict) -> None:
    save_json(SCENARIO_STATE_PATH, state)


def update_state(patch: dict) -> dict:
    state = load_state()
    state.update(patch)
    save_state(state)
    return state


def reset_state() -> dict:
    state = {
        "gps_override": None,
        "gps_path": None,
        "battery_override": None,
        "wifi_override": None,
        "disconnect": False,
        "fail_next_command": False,
    }
    save_state(state)
    return state


def consume_fail_next_command() -> bool:
    state = load_state()
    should_fail = bool(state.get("fail_next_command"))
    if should_fail:
        state["fail_next_command"] = False
        save_state(state)
    return should_fail


def consume_gps_override() -> dict | None:
    state = load_state()
    gps_path = state.get("gps_path") or []
    if gps_path:
        point = gps_path.pop(0)
        state["gps_path"] = gps_path or None
        if not gps_path:
            state["gps_override"] = point
        save_state(state)
        return point
    return state.get("gps_override")
