#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"
ANCHOR_PID_FILE="$RUNTIME_DIR/anchor.pid"
MARLIN_PID_FILE="$RUNTIME_DIR/marlin.pid"
ANCHOR_LOG="$RUNTIME_DIR/anchor.log"
MARLIN_LOG="$RUNTIME_DIR/marlin.log"

mkdir -p "$RUNTIME_DIR"
cd "$ROOT_DIR"

is_running() {
  local pid_file="$1"
  if [[ ! -f "$pid_file" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "$pid_file")"
  if [[ -z "$pid" ]]; then
    return 1
  fi

  kill -0 "$pid" 2>/dev/null
}

wait_for_port() {
  local port="$1"
  local label="$2"
  local attempts="${3:-30}"

  for _ in $(seq 1 "$attempts"); do
    if python3 - "$port" <<'PY' >/dev/null 2>&1
import socket
import sys

sock = socket.socket()
sock.settimeout(0.2)
try:
    sock.connect(("127.0.0.1", int(sys.argv[1])))
except OSError:
    raise SystemExit(1)
else:
    raise SystemExit(0)
finally:
    sock.close()
PY
    then
      return 0
    fi
    sleep 0.2
  done

  echo "$label did not open port $port in time."
  return 1
}

show_failure_logs() {
  echo
  echo "ANCHOR log tail:"
  tail -n 20 "$ANCHOR_LOG" 2>/dev/null || true
  echo
  echo "MARLIN log tail:"
  tail -n 20 "$MARLIN_LOG" 2>/dev/null || true
}

if is_running "$ANCHOR_PID_FILE" || is_running "$MARLIN_PID_FILE"; then
  echo "The stack appears to already be running."
  echo "Use ./scripts/stop_stack.sh first if you want a clean restart."
  exit 1
fi

nohup python3 -m anchor.main --serve >"$ANCHOR_LOG" 2>&1 </dev/null &
echo $! >"$ANCHOR_PID_FILE"

nohup python3 -m marlin.main --serve >"$MARLIN_LOG" 2>&1 </dev/null &
echo $! >"$MARLIN_PID_FILE"

if ! wait_for_port 8000 "ANCHOR" || ! wait_for_port 9001 "MARLIN"; then
  show_failure_logs
  exit 1
fi

python3 -m marlin.main >/dev/null 2>&1 || true

echo "ANCHOR started: http://127.0.0.1:8000"
echo "MARLIN started: http://127.0.0.1:9001"
echo "ANCHOR log: $ANCHOR_LOG"
echo "MARLIN log: $MARLIN_LOG"
echo
echo "Next:"
echo "1. Open http://127.0.0.1:8000"
echo "2. Choose baseline or anchor_managed in the top bar"
echo "3. Use the MARLIN card controls or scenario buttons to run a test"
