from __future__ import annotations

from typing import Any

import requests

try:
    from shared_ssm import get_env_or_parameter
except Exception:
    from services.shared_ssm import get_env_or_parameter


def _api_key() -> str | None:
    return get_env_or_parameter("LIVEAVATAR_API_KEY", "LIVEAVATAR_API_KEY_PARAM")


def _avatar_id() -> str | None:
    return get_env_or_parameter("LIVEAVATAR_AVATAR_ID", "LIVEAVATAR_AVATAR_ID_PARAM")


def create_session_token(avatar_id: str | None = None) -> dict[str, Any]:
    api_key = _api_key()
    avatar_id = avatar_id or _avatar_id()

    if not api_key:
        return {"created": False, "reason": "LIVEAVATAR_API_KEY_not_configured"}
    if not avatar_id:
        return {"created": False, "reason": "LIVEAVATAR_AVATAR_ID_not_configured"}

    payload = {
        "avatar_id": avatar_id,
        "mode": "LITE",
        "is_sandbox": False,
        "video_settings": {
            "quality": "high",
            "encoding": "H264",
        },
    }

    try:
        resp = requests.post(
            "https://api.liveavatar.com/v1/sessions/token",
            json=payload,
            headers={
                "X-API-KEY": api_key,
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "created": True,
            "session_id": data.get("session_id"),
            "session_token": data.get("session_token"),
        }

    except requests.HTTPError as exc:
        return {
            "created": False,
            "status_code": exc.response.status_code,
            "reason": "liveavatar_http_error",
            "body": exc.response.text,
        }

    except Exception as exc:
        return {
            "created": False,
            "reason": "liveavatar_request_failed",
            "error": str(exc),
        }


def start_session(session_token: str) -> dict[str, Any]:
    try:
        resp = requests.post(
            "https://api.liveavatar.com/v1/sessions/start",
            json={},
            headers={
                "Authorization": f"Bearer {session_token}",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "started": True,
            "livekit_url": data.get("livekit_url"),
            "livekit_token": data.get("livekit_client_token"),
        }

    except requests.HTTPError as exc:
        return {
            "started": False,
            "status_code": exc.response.status_code,
            "reason": "liveavatar_start_http_error",
            "body": exc.response.text,
        }

    except Exception as exc:
        return {
            "started": False,
            "reason": "liveavatar_start_failed",
            "error": str(exc),
        }