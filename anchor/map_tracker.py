def build_map_marker(fleet_entry: dict) -> dict:
    gps = fleet_entry.get("gps", {})
    return {
        "lat": gps.get("lat"),
        "lon": gps.get("lon"),
        "mode": fleet_entry.get("mode"),
    }
