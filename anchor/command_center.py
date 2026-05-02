from shared.anchor_command import AnchorCommand


def make_command(command_id: str, node_id: str, command_type: str, params: dict) -> AnchorCommand:
    command = AnchorCommand(
        command_id=command_id,
        node_id=node_id,
        type=command_type,
        params=params,
    )
    command.validate()
    return command


def record_command(db: dict, command: AnchorCommand) -> None:
    db["commands"].append(command.to_dict())
