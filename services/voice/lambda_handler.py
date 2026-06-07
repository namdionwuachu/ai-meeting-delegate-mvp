import json
import os
import traceback

from voice.voice_router import synthesize_voice


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Api-Key",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    """Voice-only API for POST /voice/speak."""
    try:
        body = json.loads(event.get("body") or "{}") if "body" in event else event
        text = body.get("text")
        if not text:
            return _response(400, {"error": "text is required"})

        result = synthesize_voice(
            text=text,
            voice_profile_id=body.get("voice_profile_id") or os.environ.get("DEFAULT_VOICE_PROFILE_ID", "namdi-v1"),
            meeting_id=body.get("meeting_id", "voice-demo"),
            output_mode=body.get("output_mode", "file"),
        )
        return _response(200, result)
    except Exception as exc:
        print(traceback.format_exc())
        return _response(500, {"error": str(exc)})
