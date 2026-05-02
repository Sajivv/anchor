from shared.anchor_command import AnchorCommand
from shared.command_response import CommandResponse


def accept_command(command: AnchorCommand) -> CommandResponse:
    command.validate()
    return CommandResponse(
        command_id=command.command_id,
        node_id=command.node_id,
        status="accepted",
        message="Command accepted for execution",
    )


def complete_command(
    command: AnchorCommand,
    message: str,
    result: dict | None = None,
) -> CommandResponse:
    return CommandResponse(
        command_id=command.command_id,
        node_id=command.node_id,
        status="completed",
        message=message,
        result=result or {},
    )
