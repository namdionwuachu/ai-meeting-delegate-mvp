"""SNS escalation helper."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
import boto3

_sns = None

def _client():
    global _sns
    if _sns is None:
        _sns = boto3.client("sns")
    return _sns


def escalate(payload: dict[str, Any], subject: str = "AI Delegate escalation") -> dict[str, Any]:
    topic_arn = os.environ.get("ESCALATION_TOPIC_ARN")
    if not topic_arn:
        return {"sent": False, "reason": "ESCALATION_TOPIC_ARN_not_configured"}
    body = dict(payload)
    body.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    resp = _client().publish(
        TopicArn=topic_arn,
        Subject=subject[:100],
        Message=json.dumps(body, default=str, indent=2),
    )
    return {"sent": True, "message_id": resp.get("MessageId")}
