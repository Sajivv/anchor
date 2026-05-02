# Experiment Plan

## Goal

Measure whether ANCHOR reduces required human intervention compared with a baseline MARLIN system while preserving correct mission behavior.

## Comparison Modes

- `baseline`
- `anchor_managed`

## Core Scenarios

1. `normal_drift`
- MARLIN drifts toward the mission area
- compare fixed reporting vs mission-aware passive behavior

2. `geofence_entry`
- MARLIN enters the active geofence
- compare manual operator reaction vs automatic mode transition

3. `target_wifi_detection`
- MARLIN reports a relevant nearby network
- compare manual interpretation vs ANCHOR follow-up behavior

4. `low_battery`
- MARLIN experiences low battery
- compare manual operator response vs automatic reduced activity

5. `disconnect_reconnect`
- MARLIN loses connection to ANCHOR and later reconnects
- compare degraded baseline behavior vs cached mission policy and queue replay

6. `command_failure`
- a structured command fails on MARLIN
- compare manual retry vs ANCHOR-assisted recovery handling

## Metrics

- intervention count
- scenario success/failure
- response time
- command accepted/completed/failed counts
- mode transition count
- queued outbound messages during disconnect
- reporting frequency behavior

## Graph Ideas

- intervention count by scenario: baseline vs anchor-managed
- timeline of events, commands, and mode transitions
- command outcomes by scenario
- reporting cadence across passive and active phases
