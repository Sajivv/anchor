def store_mission_config(db: dict, mission_config: dict) -> None:
    db["missions"][mission_config["node_id"]] = mission_config


def get_mission_config(db: dict, node_id: str) -> dict | None:
    return db["missions"].get(node_id)
