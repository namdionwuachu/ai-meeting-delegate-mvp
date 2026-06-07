from __future__ import annotations

import os
from typing import Any

import requests

try:
    from shared_ssm import get_env_or_parameter
except Exception:  # pragma: no cover
    from services.shared_ssm import get_env_or_parameter


def create_talk(image_url: str, audio_url: str | None = None, text: str | None = None) -> dict[str, Any]:
    api_key = get_env_or_parameter("DID_API_KEY", "DID_API_KEY_PARAM")
    if not api_key:
        return {"provider": "did", "created": False, "reason": "DID_API_KEY_not_configured"}
    payload: dict[str, Any] = {"source_url": image_url}
    if audio_url:
        payload["script"] = {"type": "audio", "audio_url": audio_url}
    else:
        payload["script"] = {"type": "text", "input": text or "Hello"}
    resp = requests.post(
        os.environ.get("DID_API_BASE_URL", "https://api.d-id.com/talks"),
        headers={"Authorization": f"Basic {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    return {"provider": "did", "created": True, "response": resp.json()}
