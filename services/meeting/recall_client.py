"""Recall.ai meeting connector skeleton.

This adapter is intentionally thin. Keep provider-specific API shapes here so the
meeting delegate remains provider-agnostic.
"""
from __future__ import annotations

import json
from typing import Any
from urllib import error, request

try:
    from shared_ssm import get_env_or_parameter
except Exception:  # pragma: no cover
    from services.shared_ssm import get_env_or_parameter


def create_bot(
    meeting_url: str,
    bot_name: str = "Namdi [AI Delegate]",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    api_key = get_env_or_parameter("RECALL_API_KEY", "RECALL_API_KEY_PARAM")

    base_url = (
        get_env_or_parameter("RECALL_API_BASE_URL", "RECALL_API_BASE_URL_PARAM")
        or "https://eu-central-1.recall.ai/api/v1"
    )

    realtime_url = get_env_or_parameter(
        "MEETING_REALTIME_URL",
        "MEETING_REALTIME_URL_PARAM",
    )

    if not api_key:
        return {
            "provider": "recall",
            "created": False,
            "reason": "RECALL_API_KEY_not_configured",
        }

    recording_config = {
        "transcript": {"provider": {"meeting_captions": {}}},
        "participant_events": {},
    }

    if realtime_url:
        recording_config["realtime_endpoints"] = [
        {
            "type": "webhook",
            "url": realtime_url,
            "events": [
                "transcript.data",
            ],
        }
    ]

    payload = {
        "meeting_url": meeting_url,
        "bot_name": bot_name,
        "metadata": metadata or {},
        "recording_config": recording_config,
    }

    url = f"{base_url.rstrip('/')}/bot/"

    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return {
                "provider": "recall",
                "created": True,
                "status_code": resp.status,
                "response": json.loads(body) if body else {},
            }

    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return {
            "provider": "recall",
            "created": False,
            "status_code": exc.code,
            "reason": "recall_http_error",
            "body": body,
        }

    except Exception as exc:
        return {
            "provider": "recall",
            "created": False,
            "reason": "recall_request_failed",
            "error": str(exc),
        }