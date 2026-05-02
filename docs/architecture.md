# Architecture Notes

## Design direction

- `MARLIN` is a remote edge node that follows its cached mission policy locally.
- `ANCHOR` is the base-station manager that receives telemetry and runs higher-order reasoning.
- `Codex` is intended to provide analyze/plan behavior through a constrained command interface rather than unrestricted shell access.

## Current prototype split

- MARLIN handles:
  - sensor reads
  - mission evaluation
  - snapshot construction
  - local caching
  - command execution
- ANCHOR handles:
  - ingest
  - fleet state
  - mission management
  - reasoning
  - policy enforcement
