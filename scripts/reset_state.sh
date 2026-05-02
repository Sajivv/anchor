#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/stop_stack.sh >/dev/null 2>&1 || true

rm -rf anchor_data marlin_cache runtime

echo "Local ANCHOR/MARLIN state cleared."
echo "Run ./scripts/start_stack.sh to recreate fresh state."
