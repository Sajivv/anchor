from math import radians, sin, cos, sqrt, atan2

from shared.mission_config import MissionConfig


def _distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = (
        sin(d_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c


def evaluate_mode(
    mission_config: MissionConfig,
    gps: dict[str, float],
    battery: dict[str, int],
) -> str:
    geofence = mission_config.active_geofence
    distance = _distance_meters(
        gps["lat"],
        gps["lon"],
        geofence.center_lat,
        geofence.center_lon,
    )
    if battery["percent"] <= 20:
        return "low_power"
    if distance <= geofence.radius_m:
        return "active"
    return "passive"
