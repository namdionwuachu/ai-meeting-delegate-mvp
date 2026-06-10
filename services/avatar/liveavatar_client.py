from __future__ import annotations

import json
from typing import Any
from urllib import error, request

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

    req = request.Request(
        "https://api.liveavatar.com/v1/sessions/token",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            data = body.get("data", {})
            return {
                "created": True,
                "session_id": data.get("session_id"),
                "session_token": data.get("session_token"),
            }

    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return {
            "created": False,
            "status_code": exc.code,
            "reason": "liveavatar_http_error",
            "body": body,
        }

    except Exception as exc:
        return {
            "created": False,
            "reason": "liveavatar_request_failed",
            "error": str(exc),
        }


def start_session(session_token: str) -> dict[str, Any]:
    req = request.Request(
        "https://api.liveavatar.com/v1/sessions/start",
        data=b"{}",
        method="POST",
        headers={
            "Authorization": f"Bearer {session_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            data = body.get("data", {})
            return {
                "started": True,
                "livekit_url": data.get("livekit_url"),
                "livekit_token": data.get("livekit_client_token"),
            }

    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return {
            "started": False,
            "status_code": exc.code,
            "reason": "liveavatar_start_http_error",
            "body": body,
        }

    except Exception as exc:
        return {
            "started": False,
            "reason": "liveavatar_start_failed",
            "error": str(exc),
        }