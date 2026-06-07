from __future__ import annotations

import json
import os
from .recall_client import create_bot
from .turn_taking import disclosure_message


def _response(status_code: int, body: dict):
    return {"statusCode": status_code, "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}, "body": json.dumps(body)}


def handler(event, context):
    body = json.loads(event.get("body") or "{}") if "body" in event else event
    meeting_url = body.get("meeting_url")
    owner_name = body.get("owner_name", os.environ.get("DEFAULT_OWNER_NAME", "Namdi Onwuachu"))
    if not meeting_url:
        return _response(400, {"error": "meeting_url is required"})
    bot = create_bot(
        meeting_url=meeting_url,
        bot_name=body.get("bot_name", f"{owner_name.split()[0]} [AI Delegate]"),
        metadata={"persona_id": body.get("persona_id", "namdi"), "owner_name": owner_name},
    )
    return _response(200, {"bot": bot, "disclosure_message": disclosure_message(owner_name)})
