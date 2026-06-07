from __future__ import annotations

import json
import os
from pathlib import Path

import boto3


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }


def _put_persona(item: dict) -> None:
    table = boto3.resource("dynamodb").Table(os.environ["PERSONA_TABLE"])
    table.put_item(Item=item)


def _put_example(item: dict) -> None:
    table = boto3.resource("dynamodb").Table(os.environ["EXAMPLES_TABLE"])
    table.put_item(Item=item)


def _put_voice_profile(item: dict) -> None:
    table = boto3.resource("dynamodb").Table(os.environ["VOICE_TABLE"])
    table.put_item(Item=item)


def handler(event, context):
    """POST /seed/persona.

    Seeds persona JSON, few-shot examples and optional voice profile.
    """
    body = json.loads(event.get("body") or "{}") if "body" in event else event
    persona = body.get("persona")
    examples = body.get("examples", [])
    voice_profile = body.get("voice_profile")

    if not persona:
        return _response(400, {"error": "persona is required"})
    if "persona_id" not in persona:
        return _response(400, {"error": "persona.persona_id is required"})

    _put_persona(persona)
    for item in examples:
        item.setdefault("persona_id", persona["persona_id"])
        _put_example(item)
    if voice_profile:
        _put_voice_profile(voice_profile)

    return _response(200, {
        "status": "seeded",
        "persona_id": persona["persona_id"],
        "examples": len(examples),
        "voice_profile": bool(voice_profile),
    })
