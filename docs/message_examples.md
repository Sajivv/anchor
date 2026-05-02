# Message Examples

## Snapshot

```json
{
  "message_type": "snapshot",
  "node_id": "marlin-01",
  "timestamp": "2026-05-01T12:00:00Z",
  "mode": "active",
  "gps": {
    "lat": 36.8501,
    "lon": -76.2859
  },
  "battery": {
    "percent": 82
  },
  "environment": {
    "temperature_c": 21.4,
    "humidity_pct": 68.2
  },
  "wifi_scan_meta": {
    "scan_performed": true,
    "scan_timestamp": "2026-05-01T11:59:50Z"
  },
  "wifi_scan": [
    {
      "ssid": "TestNet-1",
      "bssid": "AA:BB:CC:DD:EE:FF",
      "rssi": -67,
      "channel": 6
    }
  ]
}
```

## Command Response

```json
{
  "message_type": "command_response",
  "command_id": "cmd-001",
  "node_id": "marlin-01",
  "status": "completed",
  "message": "Wi-Fi scan finished",
  "result": {
    "networks_found": 1
  },
  "timestamp": "2026-05-01T12:01:00Z"
}
```
