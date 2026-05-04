from datetime import UTC, datetime
import shutil
import socket
import subprocess

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

    if sentence in {"$GPGGA", "$GNGGA"} and len(parts) >= 7 and parts[6] not in {"", "0"}:
        lat = _nmea_to_decimal(parts[2], parts[3])
        lon = _nmea_to_decimal(parts[4], parts[5])
        if lat is not None and lon is not None:
            return lat, lon

    if sentence in {"$GPGLL", "$GNGLL"} and len(parts) >= 7 and parts[6][:1] == "A":
        lat = _nmea_to_decimal(parts[1], parts[2])
        lon = _nmea_to_decimal(parts[3], parts[4])
        if lat is not None and lon is not None:
            return lat, lon

    if sentence in {"$GPGNS", "$GNGNS"} and len(parts) >= 7 and parts[6][:1] not in {"", "N"}:
        lat = _nmea_to_decimal(parts[2], parts[3])
        lon = _nmea_to_decimal(parts[4], parts[5])
        if lat is not None and lon is not None:
            return lat, lon

    return None


def _read_hotspot_gps() -> dict[str, float | str] | None:
    print(f"[gps] socket connect to {MARLIN_GPS_HOST}:{MARLIN_GPS_PORT} timeout={MARLIN_GPS_TIMEOUT_SEC}")
    with socket.create_connection(
        (MARLIN_GPS_HOST, MARLIN_GPS_PORT),
        timeout=MARLIN_GPS_TIMEOUT_SEC,
    ) as sock:
        sock.settimeout(MARLIN_GPS_TIMEOUT_SEC)
        deadline = datetime.now().timestamp() + MARLIN_GPS_TIMEOUT_SEC
        buffer = ""
        while datetime.now().timestamp() < deadline:
            try:
                chunk = sock.recv(4096)
                print(f"[gps] recv bytes={len(chunk)}")
            except TimeoutError:
                print("[gps] socket recv timeout")
                break
            if not chunk:
                print("[gps] socket returned empty chunk")
                break
            decoded = chunk.decode("ascii", errors="ignore")
            print(f"[gps] chunk sample={decoded[:120]!r}")
            buffer += decoded
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.replace("\x00", "").strip()
                if line:
                    print(f"[gps] line={line}")
                parsed = _parse_nmea_line(line)
                print(f"[gps] parsed={parsed}")
                if parsed:
                    lat, lon = parsed
                    return _mock_fix(lat=lat, lon=lon)
    return None


def _read_hotspot_gps_with_nc() -> dict[str, float | str] | None:
    nc_path = shutil.which("nc")
    print(f"[gps] nc path={nc_path}")
    if nc_path is None:
        return None

    cmd = [nc_path, "-w", "1", MARLIN_GPS_HOST, str(MARLIN_GPS_PORT)]
    print(f"[gps] running nc command={cmd}")
    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=MARLIN_GPS_TIMEOUT_SEC,
    )
    print(f"[gps] nc returncode={result.returncode}")
    print(f"[gps] nc stdout sample={(result.stdout or '')[:200]!r}")
    print(f"[gps] nc stderr sample={(result.stderr or '')[:200]!r}")

    output = result.stdout or ""
    for line in output.splitlines():
        line = line.replace("\x00", "").strip()
        if line:
            print(f"[gps] nc line={line}")
        parsed = _parse_nmea_line(line)
        print(f"[gps] nc parsed={parsed}")
        if parsed:
            lat, lon = parsed
            return _mock_fix(lat=lat, lon=lon)
    return None


def read_gps() -> dict[str, float | str]:
    override = consume_gps_override()
    print(f"[gps] source={MARLIN_GPS_SOURCE} host={MARLIN_GPS_HOST} port={MARLIN_GPS_PORT}")
    print(f"[gps] override={override}")

    if override:
        print("[gps] using scenario override")
        return _mock_fix(lat=override["lat"], lon=override["lon"])

    if MARLIN_GPS_SOURCE == "hotspot":
        try:
            hotspot_fix = _read_hotspot_gps()
            print(f"[gps] socket hotspot_fix={hotspot_fix}")
            if hotspot_fix:
                return hotspot_fix
        except OSError as exc:
            print(f"[gps] socket read failed: {exc!r}")

        try:
            hotspot_fix = _read_hotspot_gps_with_nc()
            print(f"[gps] nc hotspot_fix={hotspot_fix}")
            if hotspot_fix:
                return hotspot_fix
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"[gps] nc fallback failed: {exc!r}")

    print("[gps] falling back to mock fix")
    return _mock_fix()
Jot something down