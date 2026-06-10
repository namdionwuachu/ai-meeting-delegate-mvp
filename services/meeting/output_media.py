# services/meeting/output_media.py

from __future__ import annotations

import json
from typing import Any
from urllib import error, request

try:
    from shared_ssm import get_env_or_parameter
except Exception:  # pragma: no cover
    from services.shared_ssm import get_env_or_parameter


def _recall_config() -> tuple[str | None, str]:
    api_key = get_env_or_parameter(
        "RECALL_API_KEY",
        "RECALL_API_KEY_PARAM",
    )

    base_url = (
        get_env_or_parameter(
            "RECALL_API_BASE_URL",
            "RECALL_API_BASE_URL_PARAM",
        )
        or "https://eu-central-1.recall.ai/api/v1"
    )

    return api_key, base_url.rstrip("/")


def start_output_media(
    bot_id: str,
    webpage_url: str,
) -> dict[str, Any]:

    api_key, base_url = _recall_config()

    if not api_key:
        return {
            "started": False,
            "reason": "RECALL_API_KEY_not_configured",
        }

    if not bot_id:
        return {
            "started": False,
            "reason": "bot_id_required",
        }

    if not webpage_url:
        return {
            "started": False,
            "reason": "webpage_url_required",
        }

    payload = {
        "camera": {
            "kind": "webpage",
            "config": {
                "url": webpage_url
            }
        }
    }

    req = request.Request(
        f"{base_url}/bot/{bot_id}/output_media/",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")

            return {
                "started": True,
                "status_code": resp.status,
                "response": json.loads(body) if body else {},
            }

    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")

        return {
            "started": False,
            "status_code": exc.code,
            "reason": "recall_output_media_http_error",
            "body": body,
        }

    except Exception as exc:
        return {
            "started": False,
            "reason": "recall_output_media_failed",
            "error": str(exc),
        }
        

def start_audio_output(
    bot_id: str,
    audio_url: str,
) -> dict[str, Any]:

    api_key, base_url = _recall_config()

    if not api_key:
        return {"started": False, "reason": "RECALL_API_KEY_not_configured"}

    payload = {
        "kind": "audio",
        "audio_url": audio_url,
    }

    req = request.Request(
        f"{base_url}/bot/{bot_id}/output_audio/",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return {
                "started": True,
                "status_code": resp.status,
                "response": json.loads(body) if body else {},
            }

    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return {
            "started": False,
            "status_code": exc.code,
            "reason": "recall_audio_output_http_error",
            "body": body,
        }

    except Exception as exc:
        return {
            "started": False,
            "reason": "recall_audio_output_failed",
            "error": str(exc),
        }