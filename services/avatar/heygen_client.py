from __future__ import annotations

import os
from typing import Any

import requests

try:
    from shared_ssm import get_env_or_parameter
except Exception:  # pragma: no cover
    from services.shared_ssm import get_env_or_parameter


def _api_key() -> str | None:
    return get_env_or_parameter("HEYGEN_API_KEY", "HEYGEN_API_KEY_PARAM")


def _avatar_id() -> str | None:
    return get_env_or_parameter("HEYGEN_AVATAR_ID", "HEYGEN_AVATAR_ID_PARAM", default=os.environ.get("DEFAULT_AVATAR_ID"))


def create_session(avatar_id: str | None = None) -> dict[str, Any]:
    api_key = _api_key()
    avatar_id = avatar_id or _avatar_id()
    if not api_key:
        return {"provider": "heygen", "created": False, "reason": "HEYGEN_API_KEY_not_configured"}
    if not avatar_id:
        return {"provider": "heygen", "created": False, "reason": "HEYGEN_AVATAR_ID_not_configured"}
    resp = requests.post(
        "https://api.heygen.com/v1/streaming.new",
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json={"avatar_id": avatar_id, "quality": os.environ.get("HEYGEN_QUALITY", "medium"), "version": "v2"},
        timeout=20,
    )
    resp.raise_for_status()
    return {"provider": "heygen", "created": True, "response": resp.json()}


def send_text(session_id: str, text: str) -> dict[str, Any]:
    api_key = _api_key()
    if not api_key:
        return {"provider": "heygen", "sent": False, "reason": "HEYGEN_API_KEY_not_configured"}
    resp = requests.post(
        "https://api.heygen.com/v1/streaming.task",
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json={"session_id": session_id, "text": text},
        timeout=20,
    )
    resp.raise_for_status()
    return {"provider": "heygen", "sent": True, "response": resp.json()}
