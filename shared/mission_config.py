from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Geofence:
    type: str
    center_lat: float
    center_lon: float
    radius_m: float


@dataclass
class ReportingPolicy:
    passive_interval_sec: int
    active_interval_sec: int


@dataclass
class WifiScanPolicy:
    passive_scan_enabled: bool
    active_scan_enabled: bool
    active_scan_interval_sec: int


@dataclass
class SleepRules:
    allow_low_power_outside_geofence: bool = True
    wake_on_geofence_entry: bool = True


@dataclass
class MissionConfig:
    mission_id: str
    node_id: str
    active_geofence: Geofence
    reporting: ReportingPolicy
    wifi_scan_policy: WifiScanPolicy
    authorized_targets: list[dict[str, str]] = field(default_factory=list)
    approved_test_routines: list[str] = field(default_factory=list)
    sleep_rules: SleepRules = field(default_factory=SleepRules)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
