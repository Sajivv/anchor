# Current State

## Architecture

- `MARLIN` is a remote edge node with local sensing, mission evaluation, local caching, and structured command execution.
- `ANCHOR` is the base-station manager with ingest, fleet state, mission management, reasoning, dashboard UI, and operator chat.
- `Codex` is used as an analyze/plan component through a constrained command model rather than unrestricted shell execution.

## Working Today

- Shared protocol objects exist for:
  - mission config
  - anchor commands
  - snapshots
  - events
  - command responses
- MARLIN can:
  - build snapshots
  - queue outbound messages
  - send snapshots to ANCHOR
  - receive structured commands over HTTP
  - execute a small set of local command handlers
  - send command responses back to ANCHOR
- ANCHOR can:
  - receive snapshots, events, and command responses
  - update fleet state
  - run OpenAI-backed or mock Codex-style reasoning on selected triggers
  - issue structured commands to MARLIN
  - run in `baseline` or `anchor_managed` mode
- Dashboard can:
  - display multiple MARLINs
  - show map positions on OpenStreetMap
  - focus a MARLIN by clicking its fleet card
  - show activity and command history
  - send operator commands such as `Ping`, `Snapshot`, and `Wi-Fi Scan`
  - chat with ANCHOR through a backend endpoint
  - switch between `baseline` and `anchor_managed`
  - inject test scenarios from the MARLIN card
  - show scenario runs as they are recorded

## Run Workflow

- `python3 scripts/run_stack.py --reset`
  - clears local state
  - starts ANCHOR and MARLIN together
  - runs one initial MARLIN cycle so the dashboard has a live node immediately
  - keeps the stack alive until `Ctrl-C`
- `./scripts/reset_state.sh`
  - clears local cache, database state, and runtime pid/log files
- `./scripts/start_stack.sh`
  - alternate background workflow for local use
- `./scripts/stop_stack.sh`
  - stops both local services

## Important Limitation

- Only `marlin-01` is currently a live runnable MARLIN process.
- `marlin-02` and `marlin-03` are still demo/dashboard-only nodes.

## Current Comparison Mode

- `anchor_managed`
  - ANCHOR records telemetry
  - ANCHOR runs reasoning on selected triggers
  - ANCHOR can issue structured commands automatically
- `baseline`
  - ANCHOR records telemetry
  - ANCHOR updates fleet state and dashboard
  - ANCHOR does not auto-run reasoning or auto-issue commands

## Reasoning Backend

- `ANCHOR_REASONING_BACKEND=openai`
  - uses the OpenAI Responses API
  - requires `OPENAI_API_KEY`
  - defaults to model `gpt-5.3-codex`
- `ANCHOR_REASONING_BACKEND=mock`
  - uses the local deterministic policy in the prototype

If the OpenAI-backed path fails at runtime, the current implementation falls back to the mock policy and records a fallback reason in the reasoning result.
