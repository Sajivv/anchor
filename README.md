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
python3 scripts/run_stack.py --reset
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Keep that command running while you test. Stop it with `Ctrl-C`.

If you prefer background scripts instead, you can still use:

```bash
./scripts/reset_state.sh
./scripts/start_stack.sh
./scripts/stop_stack.sh
```

For the full local testing flow, see [docs/runbook.md](/Users/sajivgnanasekaran/Documents/New%20project/docs/runbook.md:1).

## Real OpenAI Reasoning

To use real OpenAI-backed reasoning instead of the local mock policy:

```bash
export OPENAI_API_KEY="your-key-here"
export ANCHOR_REASONING_BACKEND="openai"
export OPENAI_REASONING_MODEL="gpt-5.3-codex"
python3 scripts/run_stack.py --reset
```

Optional:

```bash
export OPENAI_REASONING_EFFORT="medium"
```

If `OPENAI_API_KEY` is not set, or the OpenAI request fails, ANCHOR falls back to the local mock reasoning policy so the prototype can still run.
