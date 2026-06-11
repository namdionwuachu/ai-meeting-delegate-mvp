from __future__ import annotations

import json
import os

import boto3
import requests

try:
    from shared_ssm import get_env_or_parameter
except Exception:
    from services.shared_ssm import get_env_or_parameter

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

    # Get audio_url and message from DynamoDB
    table = dynamodb.Table(os.environ["SESSIONS_TABLE"])
    result = table.get_item(
        Key={
            "meeting_id": bot_id,
            "event_ts": "liveavatar_token",
        }
    )
    item = result.get("Item", {})

    # Create a fresh session token on demand
    api_key = get_env_or_parameter("LIVEAVATAR_API_KEY", "LIVEAVATAR_API_KEY_PARAM")
    avatar_id = get_env_or_parameter("LIVEAVATAR_AVATAR_ID", "LIVEAVATAR_AVATAR_ID_PARAM")

    try:
        resp = requests.post(
            "https://api.liveavatar.com/v1/sessions/token",
            json={
                "avatar_id": avatar_id,
                "mode": "LITE",
                "is_sandbox": False,
                "video_settings": {"quality": "high", "encoding": "H264"},
            },
            headers={
                "X-API-KEY": api_key,
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
        session_token = data.get("session_token")
    except Exception as exc:
        return _response(500, {"error": f"LiveAvatar token creation failed: {str(exc)}"})

    return _response(200, {
        "session_token": session_token,
        "audio_url": item.get("audio_url"),
        "message": item.get("message"),
    })