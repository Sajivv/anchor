#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"
ANCHOR_PID_FILE="$RUNTIME_DIR/anchor.pid"
MARLIN_PID_FILE="$RUNTIME_DIR/marlin.pid"

stop_pid() {
  local label="$1"
  local pid_file="$2"
  if [[ ! -f "$pid_file" ]]; then
    echo "$label: not running"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    echo "$label: stopped"
  else
    echo "$label: stale pid removed"
  fi
  rm -f "$pid_file"
}

stop_pid "ANCHOR" "$ANCHOR_PID_FILE"
stop_pid "MARLIN" "$MARLIN_PID_FILE"
