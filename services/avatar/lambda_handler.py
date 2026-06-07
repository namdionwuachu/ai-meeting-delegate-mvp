from __future__ import annotations

import json
from .avatar_router import render_avatar_response


def _response(status_code: int, body: dict):
    return {"statusCode": status_code, "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}, "body": json.dumps(body)}


def handler(event, context):
    body = json.loads(event.get("body") or "{}") if "body" in event else event
    text = body.get("text")
    if not text:
        return _response(400, {"error": "text is required"})
    result = render_avatar_response(text=text, avatar_id=body.get("avatar_id"), session_id=body.get("session_id"))
    return _response(200, result)
