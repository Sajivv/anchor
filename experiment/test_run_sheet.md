# Experiment Run Sheet

Use one row per run. Fill this out while you test in the dashboard.

## Core Test Matrix

| Planned Run | Run ID | Scenario | Mode | Expected Behavior | Actual Behavior | Success? | Intervention Count | Commands Issued | Command Failures | Duration (s) | Event Count | Snapshot Count | Last Mode | Last Battery | Notes |
|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| 1 | run-001 | low_battery | baseline | Operator notices low battery and manually reduces activity. | operator observed low battery at 14% and stopped pinging | yes | 1 | 0 | 0 | 0.05 | 1 | 1 | low_power | 14 | Right now |
| 2 | run-001 | low_battery | anchor_managed | System detects low battery and shifts into low-power behavior automatically. | Low battery reached at 14%. Local MARLIN mission evaluator changed mode to low power mode. Anchor reasoning engine determined no further action required. | yes | 0 | 0 | 0 | 0.047 | 1 | 1 | low_power | 14 | no additional commands needed after low power mode started |
| 3 | run-001 | geofence_entry | baseline | Operator notices geofence entry and manually increases activity or scanning. | MARLIN started outside the geofence in passive mode, crossed into the geofence, emitted an entered_geofence event, and locally switched to active mode. Operator had to start scanning for Wi-Fi networks. | yes | 1 | 0 | 0 | 0.462 | 1 | 2 | active | 82 | Baseline mode did not issue any ANCHOR follow-up commands, so the operator would still need to decide whether additional mission activity should begin. |
| 4 | field-test-01 | geofence_entry | anchor_managed | MARLIN enters the geofence, switches behavior automatically, and ANCHOR reacts without manual input. | During the Tacoma field test, MARLIN reported live GPS while outside the geofence in passive mode, then autonomously switched to active mode on entry. ANCHOR invoked Codex reasoning and Wi-Fi scanning began automatically while the node remained inside the geofence. | yes | 0 | 0 | 0 | 583.731 | 2 | 9 | active | 58 | Reconstructed from the field log rather than a formal scenario-run export. Counts reflect the geofence-entry segment: one `mode_changed` event to active, one `entered_geofence` event, and nine active snapshots between geofence entry at `23:16:36Z` and geofence exit at `23:26:20Z`. Reasoning recommended `run_wifi_scan`, but no automatic command record was stored in the exported command list. |
| 5 | run-001 | target_wifi_detection | baseline | Operator inspects Wi-Fi results and decides whether to trigger a follow-up action. | MARLIN emitted a target-detected event and recorded a follow-up snapshot, but in baseline mode the operator would still need to interpret the detection and decide whether any follow-up action should be taken. | yes | 1 | 0 | 0 | 0.033 | 1 | 1 | passive | 82 | Baseline mode captured the target-detected event and snapshot successfully, but did not trigger any automatic follow-up action. |
| 6 | run-001 | target_wifi_detection | anchor_managed | MARLIN reports target detection and ANCHOR handles follow-up behavior automatically. | MARLIN emitted target-detected events and ANCHOR captured the follow-up snapshot automatically without operator action. | yes | 0 | 0 | 0 | 39.744 | 2 | 1 | passive | 82 | Target-detection event was recorded successfully in managed mode, but this run did not issue an additional command response. |
| 7 | run-001 | disconnect | baseline | Operator must account for the communication loss and later verify node recovery manually. | MARLIN stopped delivering telemetry to ANCHOR during the disconnect period. The disconnect run itself required manual interpretation and was superseded by the later reconnect step, where the operator verified that telemetry delivery resumed. | no | 1 | 0 | 0 | 45.713 | 0 | 0 |  |  | Disconnect was tracked as a manual-loss scenario rather than a self-contained success. Recovery was confirmed in the paired baseline reconnect run (`run-002`), which restored a passive snapshot to ANCHOR. |
| 8 | run-001 | disconnect | anchor_managed | MARLIN continues from cached mission state and the run is later finalized after validating degraded operation. | During disconnect, MARLIN stopped delivering telemetry to ANCHOR but remained in local operation. Once reconnect was triggered, telemetry automatically resumed without requiring a corrective operator command, demonstrating recovery after connectivity returned rather than autonomous network reestablishment. | no | 0 | 0 | 0 | 21.596 | 0 | 0 |  |  | Disconnect itself was manually finalized and therefore not counted as a completed run. Recovery was confirmed in the paired anchor-managed reconnect run (`run-002`), which restored a passive snapshot to ANCHOR with zero interventions. |
| 9 | run-001 | command_failure | baseline | Operator diagnoses the failed command and decides whether to retry or recover manually. | A baseline ping command was issued after `Fail Next Cmd`, but no failed command response was recorded automatically. The operator had to interpret the stalled run and manually mark it as failed. | no | 1 | 1 | 0 | 37.117 | 0 | 0 |  |  | Baseline command-failure behavior required operator intervention because the prototype did not surface a failed response back into the scenario run. |
| 10 | run-001 | command_failure | anchor_managed | MARLIN reports command failure and ANCHOR handles or records the recovery path with minimal human help. | In anchor-managed mode, a ping command was issued after `Fail Next Cmd`, but the prototype still did not record a failed command response automatically. The operator had to manually mark the run as failed, so the managed path did not yet improve failure observability in this scenario. | no | 1 | 1 | 0 | 16.79 | 0 | 0 |  |  | Anchor-managed command-failure handling remains incomplete in the current prototype because no failed command response was surfaced back into the scenario run automatically. |

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
