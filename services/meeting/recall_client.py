"""Recall.ai meeting connector skeleton.

This adapter is intentionally thin. Keep provider-specific API shapes here so the
meeting delegate remains provider-agnostic.
"""
from __future__ import annotations

import os
from typing import Any

import requests

try:
    from shared_ssm import get_env_or_parameter
except Exception:  # pragma: no cover
    from services.shared_ssm import get_env_or_parameter


def create_bot(meeting_url: str, bot_name: str = "Namdi [AI Delegate]", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    api_key = get_env_or_parameter("RECALL_API_KEY", "RECALL_API_KEY_PARAM")
    base_url = os.environ.get("RECALL_API_BASE_URL", "https://us-west-2.recall.ai/api/v1")
    if not api_key:
        return {"provider": "recall", "created": False, "reason": "RECALL_API_KEY_not_configured"}

    payload = {
        "meeting_url": meeting_url,
        "bot_name": bot_name,
        "metadata": metadata or {},
        # Provider-specific fields should be verified against your Recall region/docs.
        "recording_config": {
            "transcript": {"provider": {"meeting_captions": {}}},
            "participant_events": {},
        },
    }
    resp = requests.post(
        f"{base_url.rstrip('/')}/bot/",
        headers={"Authorization": f"Token {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    return {"provider": "recall", "created": True, "response": resp.json()}
