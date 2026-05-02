# ANCHOR / MARLIN Prototype

This repository contains a research prototype for:

- `marlin/`: the remote node runtime
- `anchor/`: the base-station runtime
- `shared/`: shared message definitions used by both sides

The project is intentionally simple and uses plain Python files so the system
architecture stays easy to understand and iterate on.

## Layout

- `shared/`: mission config, commands, snapshots, events, and command responses
- `marlin/`: sensor readers, mission evaluation, command handling, and upload flow
- `anchor/`: ingest API stubs, fleet state, mission management, reasoning, and policy checks
- `docs/`: architecture notes and message examples
- `scripts/`: helper scripts for running each side locally

## Run

```bash
python3 -m marlin.main
python3 -m anchor.main
python3 -m anchor.main --seed-demo --serve
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).
