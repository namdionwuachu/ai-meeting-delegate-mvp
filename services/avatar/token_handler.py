from __future__ import annotations

import json
import os

import boto3

dynamodb = boto3.resource("dynamodb")


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def handler(event, context):
    bot_id = (event.get("queryStringParameters") or {}).get("bot_id")
    if not bot_id:
        return _response(400, {"error": "bot_id is required"})

    table = dynamodb.Table(os.environ["SESSIONS_TABLE"])
    result = table.get_item(
        Key={
            "meeting_id": bot_id,
            "event_ts": "avatar_config",
        }
    )
    item = result.get("Item")
    if not item:
        return _response(404, {"error": "session_token not found"})

    return _response(200, {
        "session_token": item.get("session_token"),
        "audio_url": item.get("audio_url"),
        "message": item.get("message"),
    })
    