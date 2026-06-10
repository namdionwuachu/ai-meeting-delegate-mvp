from __future__ import annotations

import os

from .heygen_client import create_session


def render_avatar_response(
    text: str,
    audio_url: str | None = None,
    avatar_id: str | None = None,
    session_id: str | None = None,
) -> dict:

    avatar_id = avatar_id or os.environ.get("DEFAULT_AVATAR_ID")
    if avatar_id:
        try:
            session = (
                {"session_id": session_id}
                if session_id
                else create_session(avatar_id).get("response", {}).get("data", {})
            )
            sid = session.get("session_id") if isinstance(session, dict) else None
            if sid:
                return {
                    "mode": "heygen",
                    "session_id": sid,
                    "status": "session_created",
                    "audio_url": audio_url,
                }
            return {"mode": "voice_only", "heygen_error": "heygen_session_not_created"}
        except Exception as exc:
            return {"mode": "voice_only", "heygen_error": str(exc)}

    return {"mode": "voice_only", "heygen_error": "DEFAULT_AVATAR_ID_not_configured"}
