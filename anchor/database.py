import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any
import csv
import io


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_database(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _normalize_database(
            {
                "missions": {},
                "fleet_state": {},
                "messages": [],
                "reasoning_runs": [],
                "commands": [],
                "chat_history": [],
                "system_mode": "anchor_managed",
                "scenario_runs": [],
                "active_runs": {},
            }
        )
    return _normalize_database(json.loads(path.read_text(encoding="utf-8")))


def _normalize_database(data: dict[str, Any]) -> dict[str, Any]:
    defaults = {
        "missions": {},
        "fleet_state": {},
        "messages": [],
        "reasoning_runs": [],
        "commands": [],
        "chat_history": [],
        "system_mode": "anchor_managed",
        "scenario_runs": [],
        "active_runs": {},
    }
    for key, value in defaults.items():
        data.setdefault(key, value)
    return data


def save_database(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_normalize_database(data), indent=2), encoding="utf-8")


def append_message(db: dict[str, Any], message: dict[str, Any]) -> None:
    db["messages"].append(message)


def append_chat_message(db: dict[str, Any], role: str, text: str) -> None:
    db["chat_history"].append({"role": role, "text": text})


def start_scenario_run(db: dict[str, Any], node_id: str, scenario: str) -> dict[str, Any]:
    finalize_active_run(db, node_id, status="superseded")
    run = {
        "run_id": f"run-{len(db['scenario_runs']) + 1:03d}",
        "node_id": node_id,
        "scenario": scenario,
        "system_mode": db.get("system_mode", "anchor_managed"),
        "started_at": datetime.now(UTC).isoformat(),
        "ended_at": None,
        "status": "running",
        "events": [],
        "snapshots": [],
        "command_responses": [],
        "commands": [],
        "notes": [],
        "completed_reason": None,
        "intervention_count": 0,
        "summary": None,
    }
    db["scenario_runs"].append(run)
    db["active_runs"][node_id] = run["run_id"]
    return run


def build_run_summary(run: dict[str, Any]) -> dict[str, Any]:
    started_at = _parse_timestamp(run.get("started_at"))
    ended_at = _parse_timestamp(run.get("ended_at"))
    duration_sec = None
    if started_at and ended_at:
        duration_sec = round((ended_at - started_at).total_seconds(), 3)

    response_status_counts: dict[str, int] = {}
    for response in run.get("command_responses", []):
        status = response.get("status", "unknown")
        response_status_counts[status] = response_status_counts.get(status, 0) + 1

    event_types = [event.get("type") for event in run.get("events", []) if event.get("type")]
    last_snapshot = run.get("snapshots", [])[-1] if run.get("snapshots") else {}
    success, success_reason = evaluate_run_success(run)

    return {
        "duration_sec": duration_sec,
        "event_count": len(run.get("events", [])),
        "snapshot_count": len(run.get("snapshots", [])),
        "command_count": len(run.get("commands", [])),
        "command_response_count": len(run.get("command_responses", [])),
        "response_status_counts": response_status_counts,
        "event_types": event_types,
        "last_mode": last_snapshot.get("mode"),
        "last_battery": last_snapshot.get("battery"),
        "intervention_count": run.get("intervention_count", 0),
        "success": success,
        "success_reason": success_reason,
    }


def evaluate_run_success(run: dict[str, Any]) -> tuple[bool, str]:
    scenario = run.get("scenario")
    event_types = {event.get("type") for event in run.get("events", [])}
    snapshot_modes = [snapshot.get("mode") for snapshot in run.get("snapshots", [])]
    snapshot_batteries = [snapshot.get("battery") for snapshot in run.get("snapshots", [])]
    response_statuses = [response.get("status") for response in run.get("command_responses", [])]

    if scenario == "geofence_entry":
        if "entered_geofence" in event_types and "active" in snapshot_modes:
            return True, "Entered the geofence and reached active mode."
        return False, "Missing geofence event or active-mode snapshot."

    if scenario == "low_battery":
        if "low_battery" in event_types and "low_power" in snapshot_modes and any(
            battery is not None and battery <= 20 for battery in snapshot_batteries
        ):
            return True, "Observed low battery and low-power behavior."
        return False, "Missing low-battery event or low-power snapshot."

    if scenario == "target_wifi_detection":
        if "target_detected" in event_types and len(run.get("snapshots", [])) >= 1:
            return True, "Captured target-detection event and follow-up snapshot."
        return False, "Missing target-detected event or confirming snapshot."

    if scenario == "reconnect":
        if len(run.get("snapshots", [])) >= 1 or len(run.get("events", [])) >= 1:
            return True, "Connectivity returned and telemetry reached ANCHOR."
        return False, "No telemetry arrived after reconnect."

    if scenario == "command_failure":
        if "failed" in response_statuses:
            return True, "Observed a failed command response."
        return False, "No failed command response recorded."

    if scenario == "disconnect":
        if run.get("status") in {"completed", "manual_complete"}:
            return True, "Run was manually finalized after disconnect validation."
        return False, "Disconnect runs require manual finalization."

    if scenario in {"reset", "normal_drift"}:
        if len(run.get("snapshots", [])) >= 1:
            return True, "Captured at least one snapshot."
        return False, "No snapshot captured."

    return len(run.get("events", [])) + len(run.get("snapshots", [])) > 0, "Generic scenario summary."


def _commands_are_settled(run: dict[str, Any]) -> bool:
    commands = run.get("commands", [])
    if run.get("system_mode") != "anchor_managed" or not commands:
        return True
    return len(run.get("command_responses", [])) >= len(commands)


def should_auto_finalize(run: dict[str, Any]) -> bool:
    if run.get("status") != "running":
        return False
    scenario = run.get("scenario")
    if scenario == "disconnect":
        return False
    if scenario == "command_failure":
        return any(response.get("status") == "failed" for response in run.get("command_responses", []))
    success, _ = evaluate_run_success(run)
    return success and _commands_are_settled(run)


def finalize_run(
    run: dict[str, Any],
    *,
    status: str = "completed",
    completed_reason: str = "manual",
    intervention_count: int | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    if run.get("ended_at") is not None:
        return run
    run["ended_at"] = datetime.now(UTC).isoformat()
    run["status"] = status
    run["completed_reason"] = completed_reason
    if intervention_count is not None:
        run["intervention_count"] = intervention_count
    if note:
        run["notes"].append(note)
    run["summary"] = build_run_summary(run)
    return run


def finalize_active_run(
    db: dict[str, Any],
    node_id: str,
    status: str = "completed",
    completed_reason: str = "manual",
    intervention_count: int | None = None,
    note: str | None = None,
) -> None:
    run_id = db.get("active_runs", {}).pop(node_id, None)
    if not run_id:
        return
    run = get_run(db, run_id)
    if not run or run.get("ended_at") is not None:
        return
    finalize_run(
        run,
        status=status,
        completed_reason=completed_reason,
        intervention_count=intervention_count,
        note=note,
    )


def finalize_run_by_id(
    db: dict[str, Any],
    run_id: str,
    *,
    status: str = "completed",
    completed_reason: str = "manual",
    intervention_count: int | None = None,
    note: str | None = None,
) -> dict[str, Any] | None:
    run = get_run(db, run_id)
    if not run:
        return None
    node_id = run.get("node_id")
    if db.get("active_runs", {}).get(node_id) == run_id:
        db["active_runs"].pop(node_id, None)
    return finalize_run(
        run,
        status=status,
        completed_reason=completed_reason,
        intervention_count=intervention_count,
        note=note,
    )


def get_run(db: dict[str, Any], run_id: str) -> dict[str, Any] | None:
    for run in db["scenario_runs"]:
        if run["run_id"] == run_id:
            return run
    return None


def attach_message_to_active_run(db: dict[str, Any], message: dict[str, Any]) -> None:
    node_id = message.get("node_id")
    if not node_id:
        return
    run_id = db.get("active_runs", {}).get(node_id)
    if not run_id:
        return
    run = get_run(db, run_id)
    if not run:
        return

    message_type = message.get("message_type")
    summary = {
        "timestamp": message.get("timestamp"),
        "message_type": message_type,
    }
    if message_type == "event":
        summary["type"] = message.get("type")
        run["events"].append(summary)
    elif message_type == "snapshot":
        summary["mode"] = message.get("mode")
        summary["battery"] = (message.get("battery") or {}).get("percent")
        run["snapshots"].append(summary)
    elif message_type == "command_response":
        summary["command_id"] = message.get("command_id")
        summary["status"] = message.get("status")
        run["command_responses"].append(summary)


def attach_command_to_active_run(db: dict[str, Any], node_id: str, command: dict[str, Any]) -> None:
    run_id = db.get("active_runs", {}).get(node_id)
    if not run_id:
        return
    run = get_run(db, run_id)
    if not run:
        return
    run["commands"].append(
        {
            "command_id": command.get("command_id"),
            "type": command.get("type"),
            "issued_at": command.get("issued_at"),
        }
    )


def maybe_finalize_active_run(db: dict[str, Any], node_id: str) -> dict[str, Any] | None:
    run_id = db.get("active_runs", {}).get(node_id)
    if not run_id:
        return None
    run = get_run(db, run_id)
    if not run or not should_auto_finalize(run):
        return None
    db["active_runs"].pop(node_id, None)
    return finalize_run(run, status="completed", completed_reason="auto")


def export_run_rows(db: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in db.get("scenario_runs", []):
        summary = run.get("summary") or build_run_summary(run)
        response_counts = summary.get("response_status_counts", {})
        rows.append(
            {
                "run_id": run.get("run_id"),
                "node_id": run.get("node_id"),
                "scenario": run.get("scenario"),
                "system_mode": run.get("system_mode"),
                "status": run.get("status"),
                "completed_reason": run.get("completed_reason"),
                "started_at": run.get("started_at"),
                "ended_at": run.get("ended_at"),
                "duration_sec": summary.get("duration_sec"),
                "success": summary.get("success"),
                "success_reason": summary.get("success_reason"),
                "event_count": summary.get("event_count"),
                "snapshot_count": summary.get("snapshot_count"),
                "command_count": summary.get("command_count"),
                "command_response_count": summary.get("command_response_count"),
                "accepted_count": response_counts.get("accepted", 0),
                "completed_count": response_counts.get("completed", 0),
                "failed_count": response_counts.get("failed", 0),
                "rejected_count": response_counts.get("rejected", 0),
                "intervention_count": summary.get("intervention_count", 0),
                "last_mode": summary.get("last_mode"),
                "last_battery": summary.get("last_battery"),
                "event_types": "|".join(summary.get("event_types", [])),
                "notes": " | ".join(run.get("notes", [])),
            }
        )
    return rows


def export_aggregate_rows(db: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for row in export_run_rows(db):
        key = (str(row["scenario"]), str(row["system_mode"]))
        entry = grouped.setdefault(
            key,
            {
                "scenario": row["scenario"],
                "system_mode": row["system_mode"],
                "run_count": 0,
                "success_count": 0,
                "failed_run_count": 0,
                "total_interventions": 0,
                "avg_duration_sec": 0.0,
                "total_events": 0,
                "total_snapshots": 0,
                "total_commands": 0,
                "total_command_responses": 0,
            },
        )
        entry["run_count"] += 1
        entry["success_count"] += 1 if row.get("success") else 0
        entry["failed_run_count"] += 1 if row.get("status") == "failed" else 0
        entry["total_interventions"] += int(row.get("intervention_count") or 0)
        entry["total_events"] += int(row.get("event_count") or 0)
        entry["total_snapshots"] += int(row.get("snapshot_count") or 0)
        entry["total_commands"] += int(row.get("command_count") or 0)
        entry["total_command_responses"] += int(row.get("command_response_count") or 0)
        entry["avg_duration_sec"] += float(row.get("duration_sec") or 0.0)

    aggregate_rows = []
    for entry in grouped.values():
        run_count = entry["run_count"] or 1
        aggregate_rows.append(
            {
                **entry,
                "success_rate": round(entry["success_count"] / run_count, 4),
                "avg_duration_sec": round(entry["avg_duration_sec"] / run_count, 3),
                "avg_interventions": round(entry["total_interventions"] / run_count, 3),
            }
        )
    aggregate_rows.sort(key=lambda row: (row["scenario"], row["system_mode"]))
    return aggregate_rows


def export_summary_payload(db: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "run_rows": export_run_rows(db),
        "aggregate_rows": export_aggregate_rows(db),
    }


def export_run_rows_csv(db: dict[str, Any]) -> str:
    rows = export_run_rows(db)
    fieldnames = [
        "run_id",
        "node_id",
        "scenario",
        "system_mode",
        "status",
        "completed_reason",
        "started_at",
        "ended_at",
        "duration_sec",
        "success",
        "success_reason",
        "event_count",
        "snapshot_count",
        "command_count",
        "command_response_count",
        "accepted_count",
        "completed_count",
        "failed_count",
        "rejected_count",
        "intervention_count",
        "last_mode",
        "last_battery",
        "event_types",
        "notes",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()
