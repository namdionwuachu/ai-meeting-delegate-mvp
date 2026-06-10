# services/meeting/realtime_handler.py

from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3

from .turn_taking import should_respond


lambda_client = boto3.client("lambda")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _response(status_code: int, body: dict[str, Any]):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def _safe_json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {"raw_body": value}


def _extract_text(payload: dict[str, Any]) -> str:
    """
    Best-effort extraction because Recall realtime payload shape may vary
    depending on configuration.
    """
    candidates = [
        payload.get("text"),
        payload.get("transcript"),
        payload.get("words"),
        payload.get("data", {}).get("text") if isinstance(payload.get("data"), dict) else None,
        payload.get("data", {}).get("transcript") if isinstance(payload.get("data"), dict) else None,
        payload.get("event", {}).get("text") if isinstance(payload.get("event"), dict) else None,
    ]
    
    

    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Handle Recall's nested data.data.words structure
    data = payload.get("data")
    if isinstance(data, dict):
        inner_data = data.get("data")
        if isinstance(inner_data, dict):
            words = inner_data.get("words")
            if isinstance(words, list):
                return " ".join(
                    str(w.get("text") or "").strip()
                    for w in words
                    if isinstance(w, dict)
                ).strip()

    return ""
    

def handler(event, context):
    logger.info("Recall realtime event received")
    logger.info(json.dumps(event))

    body = _safe_json_loads(event.get("body"))

    transcript_text = _extract_text(body)
    turn_decision = should_respond(transcript_text)

    logger.info(
        json.dumps(
            {
                "transcript_text": transcript_text,
                "turn_decision": turn_decision,
            }
        )
    )
    
    # Ignore the bot's own speech to prevent feedback loops
    participant_name = (
        (body.get("data") or {})
        .get("data", {})
        .get("participant", {})
        .get("name", "")
        .lower()
    )
    if "ai delegate" in participant_name or "namdi ai" in participant_name:
        return _response(200, {"received": True, "skipped": "bot_own_speech"})
    
    if turn_decision.get("respond") and transcript_text:
        bot_id = (
            body.get("bot_id")
            or (body.get("data") or {}).get("bot_id")
            or (((body.get("data") or {}).get("bot") or {})).get("id")
        )

        lambda_client.invoke(
            FunctionName=os.environ["ORCHESTRATOR_FUNCTION_NAME"],
            InvocationType="Event",
            Payload=json.dumps({
                "source": "realtime",
                "transcript": transcript_text,
                "bot_id": bot_id,
            }).encode(),
        )

        logger.info(f"Triggered orchestrator for bot {bot_id}")


    return _response(
        200,
        {
            "received": True,
            "transcript_text": transcript_text,
            "turn_decision": turn_decision,
        },
    )