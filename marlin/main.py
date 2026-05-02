from shared.mission_config import Geofence, MissionConfig, ReportingPolicy, SleepRules, WifiScanPolicy

from marlin import battery_reader, gps_reader, temp_humidity_reader, wifi_scanner
from marlin.config import MISSION_CONFIG_PATH, NODE_STATE_PATH, OUTBOUND_QUEUE_PATH
from marlin.local_store import load_json, save_json
from marlin.mission_evaluator import evaluate_mode
from marlin.snapshot_builder import build_snapshot
from marlin.uploader import queue_message


def default_mission_config() -> MissionConfig:
    return MissionConfig(
        mission_id="mission-001",
        node_id="marlin-01",
        active_geofence=Geofence(
            type="circle",
            center_lat=38.9445,
            center_lon=-76.4367,
            radius_m=750,
        ),
        reporting=ReportingPolicy(
            passive_interval_sec=1800,
            active_interval_sec=120,
        ),
        wifi_scan_policy=WifiScanPolicy(
            passive_scan_enabled=False,
            active_scan_enabled=True,
            active_scan_interval_sec=60,
        ),
        approved_test_routines=["wifi_scan", "wifi_monitor", "metadata_capture"],
        sleep_rules=SleepRules(),
    )


def main() -> None:
    stored_config = load_json(MISSION_CONFIG_PATH)
    if stored_config:
        node_id = stored_config["node_id"]
        geofence = stored_config["active_geofence"]
        reporting = stored_config["reporting"]
        scan_policy = stored_config["wifi_scan_policy"]
        mission_config = MissionConfig(
            mission_id=stored_config["mission_id"],
            node_id=node_id,
            active_geofence=Geofence(**geofence),
            reporting=ReportingPolicy(**reporting),
            wifi_scan_policy=WifiScanPolicy(**scan_policy),
            authorized_targets=stored_config.get("authorized_targets", []),
            approved_test_routines=stored_config.get("approved_test_routines", []),
            sleep_rules=SleepRules(**stored_config.get("sleep_rules", {})),
        )
    else:
        mission_config = default_mission_config()
        save_json(MISSION_CONFIG_PATH, mission_config.to_dict())

    gps = gps_reader.read_gps()
    battery = battery_reader.read_battery()
    environment = temp_humidity_reader.read_temperature_humidity()
    mode = evaluate_mode(mission_config, gps, battery)

    if mode == "active" or mission_config.wifi_scan_policy.passive_scan_enabled:
        wifi_scan_meta, wifi_scan = wifi_scanner.scan_wifi()
    else:
        wifi_scan_meta, wifi_scan = {"scan_performed": False}, []

    snapshot = build_snapshot(
        node_id=mission_config.node_id,
        mode=mode,
        gps=gps,
        battery=battery,
        environment=environment,
        wifi_scan_meta=wifi_scan_meta,
        wifi_scan=wifi_scan,
    )
    save_json(
        NODE_STATE_PATH,
        {
            "node_id": mission_config.node_id,
            "mode": mode,
            "gps": snapshot.gps,
            "battery": snapshot.battery,
            "environment": snapshot.environment,
            "wifi_scan_meta": snapshot.wifi_scan_meta,
        },
    )
    queue_message(OUTBOUND_QUEUE_PATH, snapshot.to_dict())
    print(f"Queued snapshot for {mission_config.node_id} in mode={mode}")


if __name__ == "__main__":
    main()
