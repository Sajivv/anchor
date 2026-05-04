from datetime import UTC, datetime
import socket

from marlin.config import (
    MARLIN_GPS_HOST,
    MARLIN_GPS_PORT,
    MARLIN_GPS_SOURCE,
    MARLIN_GPS_TIMEOUT_SEC,
)
from marlin.scenario_state import consume_gps_override


DEFAULT_LAT = 38.9345
DEFAULT_LON = -76.4367


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _mock_fix(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> dict[str, float | str]:
    return {
        "lat": lat,
        "lon": lon,
        "fix_timestamp": _now(),
    }


def _nmea_to_decimal(raw_value: str, hemisphere: str) -> float | None:
    if not raw_value or not hemisphere:
        return None

    try:
        numeric = float(raw_value)
    except ValueError:
        return None

    degrees = int(numeric // 100)
    minutes = numeric - (degrees * 100)
    decimal = degrees + (minutes / 60)

    if hemisphere in {"S", "W"}:
        decimal *= -1
    return decimal


def _parse_nmea_line(line: str) -> tuple[float, float] | None:
    if not line.startswith("$"):
        return None

    parts = line.split(",")
    sentence = parts[0]

    if sentence in {"$GPRMC", "$GNRMC"} and len(parts) >= 7 and parts[2] == "A":
        lat = _nmea_to_decimal(parts[3], parts[4])
        lon = _nmea_to_decimal(parts[5], parts[6])
        if lat is not None and lon is not None:
            return lat, lon

    if sentence in {"$GPGGA", "$GNGGA"} and len(parts) >= 6 and parts[6] not in {"", "0"}:
        lat = _nmea_to_decimal(parts[2], parts[3])
        lon = _nmea_to_decimal(parts[4], parts[5])
        if lat is not None and lon is not None:
            return lat, lon

    if sentence in {"$GPGLL", "$GNGLL"} and len(parts) >= 7 and parts[6][:1] == "A":
        lat = _nmea_to_decimal(parts[1], parts[2])
        lon = _nmea_to_decimal(parts[3], parts[4])
        if lat is not None and lon is not None:
            return lat, lon

    if sentence in {"$GPGNS", "$GNGNS"} and len(parts) >= 6 and parts[6][:1] not in {"", "N"}:
        lat = _nmea_to_decimal(parts[2], parts[3])
        lon = _nmea_to_decimal(parts[4], parts[5])
        if lat is not None and lon is not None:
            return lat, lon

    return None


def _read_hotspot_gps() -> dict[str, float | str] | None:
    with socket.create_connection(
        (MARLIN_GPS_HOST, MARLIN_GPS_PORT),
        timeout=MARLIN_GPS_TIMEOUT_SEC,
    ) as sock:
        sock.settimeout(MARLIN_GPS_TIMEOUT_SEC)
        with sock.makefile("r", encoding="ascii", errors="ignore") as stream:
            deadline = datetime.now().timestamp() + MARLIN_GPS_TIMEOUT_SEC
            while datetime.now().timestamp() < deadline:
                line = stream.readline()
                if not line:
                    break
                parsed = _parse_nmea_line(line.strip())
                if parsed:
                    lat, lon = parsed
                    return _mock_fix(lat=lat, lon=lon)
    return None


def read_gps() -> dict[str, float | str]:
    override = consume_gps_override()
    if override:
        return _mock_fix(lat=override["lat"], lon=override["lon"])

    if MARLIN_GPS_SOURCE == "hotspot":
        try:
            hotspot_fix = _read_hotspot_gps()
            if hotspot_fix:
                return hotspot_fix
        except OSError:
            pass

    return _mock_fix()
