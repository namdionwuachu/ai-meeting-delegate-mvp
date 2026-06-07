from __future__ import annotations

import os
from .heygen_client import create_streaming_session, speak as heygen_speak
from .did_client import create_talk


def render_avatar_response(text: str, avatar_id: str | None = None, session_id: str | None = None) -> dict:
    avatar_id = avatar_id or os.environ.get("DEFAULT_AVATAR_ID")
    if avatar_id:
        try:
            session = {"session_id": session_id} if session_id else create_streaming_session(avatar_id).get("response", {}).get("data", {})
            sid = session.get("session_id") if isinstance(session, dict) else None
            if sid:
                return {"mode": "heygen", "session_id": sid, "task": heygen_speak(sid, text)}
        except Exception as exc:
            heygen_error = str(exc)
        else:
            heygen_error = "heygen_session_not_created"
    else:
        heygen_error = "DEFAULT_AVATAR_ID_not_configured"

    try:
        return {"mode": "did_fallback", "heygen_error": heygen_error, "task": create_talk(text)}
    except Exception as exc:
        return {"mode": "voice_only", "heygen_error": heygen_error, "did_error": str(exc)}
