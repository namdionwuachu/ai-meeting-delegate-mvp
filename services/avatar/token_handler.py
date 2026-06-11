from __future__ import annotations

import json
import os
import urllib.request

import boto3

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

    api_key = get_env_or_parameter("LIVEAVATAR_API_KEY", "LIVEAVATAR_API_KEY_PARAM")
    avatar_id = get_env_or_parameter("LIVEAVATAR_AVATAR_ID", "LIVEAVATAR_AVATAR_ID_PARAM")

    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    # Create fresh session token
    try:
        payload = json.dumps({
            "avatar_id": avatar_id,
            "mode": "LITE",
            "is_sandbox": False,
            "video_settings": {"quality": "high", "encoding": "H264"},
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.liveavatar.com/v1/sessions/token",
            data=payload,
            method="POST",
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8")).get("data", {})
            session_token = data.get("session_token")
    except Exception as exc:
        return _response(500, {"error": f"Token creation failed: {str(exc)}"})

    # Start session to get LiveKit credentials
    try:
        start_req = urllib.request.Request(
            "https://api.liveavatar.com/v1/sessions/start",
            data=b"{}",
            method="POST",
            headers={
                "Authorization": f"Bearer {session_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
        )
        with urllib.request.urlopen(start_req, timeout=15) as start_resp:
            start_data = json.loads(start_resp.read().decode("utf-8")).get("data", {})
            livekit_url = start_data.get("livekit_url")
            livekit_token = start_data.get("livekit_client_token")
    except Exception as exc:
        return _response(500, {"error": f"Session start failed: {str(exc)}"})

    # Build WebSocket URL for sending audio to avatar
    ws_url = f"wss://api.liveavatar.com/v1/sessions/ws?token={session_token}"

    return _response(200, {
        "session_token": session_token,
        "livekit_url": livekit_url,
        "livekit_token": livekit_token,
        "ws_url": ws_url,
        "audio_url": item.get("audio_url"),
        "message": item.get("message"),
    })
