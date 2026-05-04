# Experiment Run Sheet

Use one row per run. Fill this out while you test in the dashboard.

## Core Test Matrix

| Planned Run | Run ID | Scenario | Mode | Expected Behavior | Actual Behavior | Success? | Intervention Count | Commands Issued | Command Failures | Duration (s) | Event Count | Snapshot Count | Last Mode | Last Battery | Notes |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| 1 | run-001 | low_battery | baseline | Operator notices low battery and manually reduces activity. | operator observed low battery at 14% and stopped pinging | yes | 1 | 0 | 0 | 0.05 | 1 | 1 | low_power | 14 | Right now |
| 2 | run-001 | low_battery | anchor_managed | System detects low battery and shifts into low-power behavior automatically. | Low battery reached at 14%. Local MARLIN mission evaluator changed mode to low power mode. Anchor reasoning engine determined no further action required. | yes | 0 | 0 | 0 | 0.047 | 1 | 1 | low_power | 14 | no additional commands needed after low power mode started |
| 3 | run-001 | geofence_entry | baseline | Operator notices geofence entry and manually increases activity or scanning. | MARLIN started outside the geofence in passive mode, crossed into the geofence, emitted an entered_geofence event, and locally switched to active mode. Operator had to start scanning for Wi-Fi networks. | yes | 1 | 0 | 0 | 0.462 | 1 | 2 | active | 82 | Baseline mode did not issue any ANCHOR follow-up commands, so the operator would still need to decide whether additional mission activity should begin. |
| 4 |  | geofence_entry | anchor_managed | MARLIN enters the geofence, switches behavior automatically, and ANCHOR reacts without manual input. |  |  |  |  |  |  |  |  |  |  |  |
| 5 |  | target_wifi_detection | baseline | Operator inspects Wi-Fi results and decides whether to trigger a follow-up action. |  |  |  |  |  |  |  |  |  |  |  |
| 6 |  | target_wifi_detection | anchor_managed | MARLIN reports target detection and ANCHOR handles follow-up behavior automatically. |  |  |  |  |  |  |  |  |  |  |  |
| 7 |  | disconnect | baseline | Operator must account for the communication loss and later verify node recovery manually. |  |  |  |  |  |  |  |  |  |  |  |
| 8 |  | disconnect | anchor_managed | MARLIN continues from cached mission state and the run is later finalized after validating degraded operation. |  |  |  |  |  |  |  |  |  |  |  |
| 9 |  | command_failure | baseline | Operator diagnoses the failed command and decides whether to retry or recover manually. |  |  |  |  |  |  |  |  |  |  |  |
| 10 |  | command_failure | anchor_managed | MARLIN reports command failure and ANCHOR handles or records the recovery path with minimal human help. |  |  |  |  |  |  |  |  |  |  |  |

## How To Use This Sheet

1. Start clean with:

```bash
python3 scripts/run_stack.py --reset
```

2. Open the ANCHOR dashboard at `http://127.0.0.1:8000`.
3. Set the mode to `baseline` or `anchor_managed`.
4. Trigger the scenario on `marlin-01`.
5. Watch the `Scenario Runs` panel.
6. If the run stays open, finalize it and enter the intervention count.
7. Export JSON or CSV if you want to cross-check the values.
8. Fill in the row for that run.

## Suggested Meaning Of Columns

- `Run ID`: the real ANCHOR run id, like `run-001`
- `Success?`: `yes` or `no`
- `Intervention Count`: how many times a human had to step in
- `Commands Issued`: number of commands ANCHOR sent during the run
- `Command Failures`: number of failed command responses
- `Duration (s)`: from the run summary
- `Event Count`: from the run summary
- `Snapshot Count`: from the run summary
- `Last Mode`: the final MARLIN mode seen in the run
- `Last Battery`: the final battery level seen in the run

## Optional Summary Table

You can fill this in after all 10 runs are done.

| Scenario | Baseline Interventions | ANCHOR Interventions | Baseline Success | ANCHOR Success | Notes |
|---|---:|---:|---|---|---|
| low_battery |  |  |  |  |  |
| geofence_entry |  |  |  |  |  |
| target_wifi_detection |  |  |  |  |  |
| disconnect |  |  |  |  |  |
| command_failure |  |  |  |  |  |
