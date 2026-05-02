from shared.anchor_command import VALID_COMMAND_TYPES, VALID_MODES


def evaluate_action(action: dict, confidence: float) -> tuple[bool, str]:
    if confidence < 0.75:
        return False, "Confidence below auto-approval threshold"

    action_type = action.get("type")
    if action_type not in VALID_COMMAND_TYPES:
        return False, "Unsupported command type"

    if action_type == "set_mode":
        mode = action.get("params", {}).get("mode")
        if mode not in VALID_MODES:
            return False, "Unsupported mode"

    return True, "Approved"
