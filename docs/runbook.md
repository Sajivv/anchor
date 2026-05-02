# Runbook

## Clean Local Start

The cleanest way to run the whole prototype locally is:

```bash
python3 scripts/run_stack.py --reset
```

Then open:

- `http://127.0.0.1:8000` for the ANCHOR dashboard

This stack runner:

- starts ANCHOR on port `8000`
- starts MARLIN on port `9001`
- runs one MARLIN telemetry cycle so the dashboard immediately sees a live node
- keeps both services alive until you press `Ctrl-C`

## Stop the Stack

If you used `python3 scripts/run_stack.py --reset`, stop it with `Ctrl-C`.

If you used the background helper scripts instead:

```bash
./scripts/stop_stack.sh
```

## Logs

When the stack is started with either workflow, logs are written to:

- `runtime/anchor.log`
- `runtime/marlin.log`

## Manual Run Flow

1. Start the stack.
2. Open the dashboard.
3. Pick `baseline` or `anchor_managed` in the top bar.
4. Use the scenario buttons on `marlin-01` to inject:
   - `Geofence`
   - `Low Battery`
   - `Target Wi-Fi`
   - `Disconnect`
   - `Reconnect`
   - `Fail Next Cmd`
   - `Reset`
5. Watch:
   - `Scenario Runs`
   - fleet state
   - activity feed
   - map movement

## Suggested Experiment Loop

For each scenario:

1. `./scripts/reset_state.sh`
2. `python3 scripts/run_stack.py --reset`
3. Set dashboard mode to `baseline`
4. Run the scenario and record results
5. Repeat from a clean reset
6. Set dashboard mode to `anchor_managed`
7. Run the same scenario and record results

This keeps the two runs comparable and avoids stale state carrying over between experiments.
