# services/meeting/output_media_handler.py

from __future__ import annotations

import json
import logging
from typing import Any

from .output_media import start_output_media

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


def handler(event, context):
    logger.info("Output media request received")
    logger.info(json.dumps(event))

    try:
        body = (
            json.loads(event.get("body") or "{}")
            if isinstance(event, dict)
            else {}
        )

        bot_id = body.get("bot_id")
        webpage_url = body.get("webpage_url")

        if not bot_id:
            return _response(400, {"error": "bot_id is required"})

        if not webpage_url:
            return _response(400, {"error": "webpage_url is required"})

        result = start_output_media(
            bot_id=bot_id,
            webpage_url=webpage_url,
        )

        return _response(
            200 if result.get("started") else 502,
            {"output_media": result},
        )

    except Exception as exc:
        logger.exception("Output media failed")
        return _response(500, {"error": str(exc)})