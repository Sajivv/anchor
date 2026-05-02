#!/usr/bin/env python3
from __future__ import annotations

import argparse
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = ROOT_DIR / "runtime"
ANCHOR_LOG = RUNTIME_DIR / "anchor.log"
MARLIN_LOG = RUNTIME_DIR / "marlin.log"


def wait_for_port(port: int, timeout_sec: float = 8.0) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            try:
                sock.connect(("127.0.0.1", port))
            except OSError:
                time.sleep(0.2)
                continue
            return True
    return False


def reset_state() -> None:
    for relative in ("anchor_data", "marlin_cache", "runtime"):
        path = ROOT_DIR / relative
        if not path.exists():
            continue
        if path.is_dir():
            for child in sorted(path.rglob("*"), reverse=True):
                if child.is_file() or child.is_symlink():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
            path.rmdir()
        else:
            path.unlink()


def launch_process(args: list[str], log_path: Path) -> subprocess.Popen[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")
    return subprocess.Popen(
        args,
        cwd=ROOT_DIR,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
    )


def terminate_process(process: subprocess.Popen[str] | None, label: str) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)
    print(f"{label} stopped.")


def print_log_tail(path: Path, label: str) -> None:
    print()
    print(f"{label} log tail:")
    if not path.exists():
        print("(no log file)")
        return
    lines = path.read_text(encoding="utf-8").splitlines()[-20:]
    if not lines:
        print("(empty)")
        return
    for line in lines:
        print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ANCHOR and MARLIN together")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear local state before launching the stack",
    )
    args = parser.parse_args()

    if args.reset:
        reset_state()
        print("Local state cleared.")

    anchor_process: subprocess.Popen[str] | None = None
    marlin_process: subprocess.Popen[str] | None = None

    def shutdown(*_: object) -> None:
        terminate_process(anchor_process, "ANCHOR")
        terminate_process(marlin_process, "MARLIN")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    anchor_process = launch_process(
        [sys.executable, "-m", "anchor.main", "--serve"],
        ANCHOR_LOG,
    )
    marlin_process = launch_process(
        [sys.executable, "-m", "marlin.main", "--serve"],
        MARLIN_LOG,
    )

    if not wait_for_port(8000) or not wait_for_port(9001):
        print("The local stack did not start correctly.")
        print_log_tail(ANCHOR_LOG, "ANCHOR")
        print_log_tail(MARLIN_LOG, "MARLIN")
        terminate_process(anchor_process, "ANCHOR")
        terminate_process(marlin_process, "MARLIN")
        return 1

    bootstrap = subprocess.run(
        [sys.executable, "-m", "marlin.main"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )
    if bootstrap.stdout.strip():
        print(bootstrap.stdout.strip())
    if bootstrap.returncode != 0:
        print("Initial MARLIN bootstrap cycle failed.")
        if bootstrap.stderr.strip():
            print(bootstrap.stderr.strip())
        terminate_process(anchor_process, "ANCHOR")
        terminate_process(marlin_process, "MARLIN")
        return 1

    print("ANCHOR started: http://127.0.0.1:8000")
    print("MARLIN started: http://127.0.0.1:9001")
    print(f"ANCHOR log: {ANCHOR_LOG}")
    print(f"MARLIN log: {MARLIN_LOG}")
    print()
    print("Keep this command running while you test.")
    print("Press Ctrl-C to stop both services.")

    while True:
        if anchor_process.poll() is not None or marlin_process.poll() is not None:
            print("One of the services exited unexpectedly.")
            print_log_tail(ANCHOR_LOG, "ANCHOR")
            print_log_tail(MARLIN_LOG, "MARLIN")
            terminate_process(anchor_process, "ANCHOR")
            terminate_process(marlin_process, "MARLIN")
            return 1
        time.sleep(1)


if __name__ == "__main__":
    raise SystemExit(main())
