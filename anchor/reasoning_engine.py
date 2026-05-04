import json
from urllib import request
from urllib.error import HTTPError, URLError

from anchor.config import (
    ANCHOR_REASONING_BACKEND,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_REASONING_EFFORT,
    OPENAI_REASONING_MODEL,
)


def should_trigger_reasoning(message: dict) -> bool:
    trigger_events = {
        "entered_geofence",
        "left_geofence",
        "target_detected",
        "low_battery",
        "command_failed",
    }
    if message.get("message_type") == "event":
        return message.get("type") in trigger_events
    return False


def build_reasoning_context(
    message: dict,
    fleet_entry: dict,
    mission_config: dict | None,
) -> dict:
    node_battery = fleet_entry.get("battery")
    if message.get("message_type") == "event" and message.get("type") == "low_battery":
        battery_percent = (message.get("details") or {}).get("battery_percent")
        if battery_percent is not None:
            node_battery = {"percent": battery_percent}

    return {
        "trigger": {
            "type": message.get("type", message.get("message_type")),
            "timestamp": message.get("timestamp"),
        },
        "node_summary": {
            "node_id": message.get("node_id"),
            "mode": fleet_entry.get("mode"),
            "gps": fleet_entry.get("gps"),
            "battery": node_battery,
        },
        "mission_config": mission_config,
        "event_details": message.get("details", {}),
        "recent_history": {
            "recent_events": [],
            "recent_commands": [],
            "recent_snapshots": [],
        },
        "allowed_actions": [
            "update_mission_config",
            "request_snapshot",
            "set_mode",
            "sleep_until",
            "run_wifi_scan",
            "start_wifi_monitor",
            "stop_wifi_activity",
            "ping",
        ],
    }


def _default_result(summary: str, *, confidence: float = 0.8) -> dict:
    return {
        "summary": summary,
        "recommended_actions": [],
        "mission_config_patch": None,
        "confidence": confidence,
    }


def _mock_reason(context: dict) -> dict:
    trigger_type = context["trigger"]["type"]
    if trigger_type == "entered_geofence":
        result = {
            "summary": "Node entered the active geofence and should begin active scanning.",
            "recommended_actions": [
                {
                    "type": "run_wifi_scan",
                    "params": {"duration_sec": 60, "channels": [1, 6, 11]},
                }
            ],
            "mission_config_patch": None,
            "confidence": 0.9,
        }
    else:
        result = _default_result("No action needed.")
    result["backend"] = "mock"
    result["model"] = "local-policy"
    return result


def _reasoning_instructions() -> str:
    return (
        "You are ANCHOR, the Analyze/Plan reasoning engine for a maritime autonomic system. "
        "You must choose from the provided allowed_actions only. "
        "Return no more than one immediate action unless a second action is clearly required. "
        "If MARLIN already handled the condition locally, prefer no further action. "
        "For low battery, avoid aggressive activity increases. "
        "For geofence entry, a Wi-Fi scan is usually appropriate. "
        "Return only valid JSON with the keys summary, recommended_actions, mission_config_patch, and confidence. "
        "Do not wrap the JSON in markdown fences."
    )


def _extract_response_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return payload["output_text"]
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                return content["text"]
    raise ValueError("No output text found in OpenAI response payload")


def _call_openai_reasoning(context: dict) -> dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    body = {
        "model": OPENAI_REASONING_MODEL,
        "reasoning": {"effort": OPENAI_REASONING_EFFORT},
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": _reasoning_instructions()}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(context, indent=2),
                    }
                ],
            },
        ],
        "text": {"format": {"type": "text"}},
    }

    req = request.Request(
        url=f"{OPENAI_BASE_URL.rstrip('/')}/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {error_body}") from exc

    response_text = _extract_response_text(payload)
    result = json.loads(response_text)
    result["backend"] = "openai"
    result["model"] = OPENAI_REASONING_MODEL
    result["response_id"] = payload.get("id")
    return result


def reason(context: dict) -> dict:
    if ANCHOR_REASONING_BACKEND == "openai":
        try:
            return _call_openai_reasoning(context)
        except (HTTPError, URLError, TimeoutError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            result = _mock_reason(context)
            result["fallback_reason"] = str(exc)
            return result
    return _mock_reason(context)
