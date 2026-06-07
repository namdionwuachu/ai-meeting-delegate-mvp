from __future__ import annotations

import json
import time
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError

from persona.model_config import get_model_config
from persona.token_budget import check_token_budget


class BedrockInvocationError(RuntimeError):
    pass


def _client(config):
    return boto3.client(
        "bedrock-runtime",
        config=Config(
            read_timeout=config.read_timeout_seconds,
            connect_timeout=config.connect_timeout_seconds,
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    )


def invoke_bedrock(prompt: str) -> dict[str, Any]:
    """Invoke Claude messages API on Bedrock with token/cost guardrails.

    Returns a structured payload containing answer text and usage metadata.
    """
    cfg = get_model_config()
    budget = check_token_budget(prompt, cfg.max_tokens)
    if not budget.allowed:
        raise BedrockInvocationError(f"Bedrock budget blocked request: {budget.reason}")

    body = {
        "anthropic_version": cfg.anthropic_version,
        "max_tokens": cfg.max_tokens,
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
    }

    started = time.time()
    try:
        response = _client(cfg).invoke_model(
            modelId=cfg.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        latency_ms = int((time.time() - started) * 1000)
        payload = json.loads(response["body"].read())
        text = "".join(part.get("text", "") for part in payload.get("content", []) if part.get("type") == "text")
        usage = payload.get("usage", {})
        return {
            "text": text.strip(),
            "model_id": cfg.model_id,
            "latency_ms": latency_ms,
            "usage": usage,
            "budget": budget.__dict__,
        }
    except (ClientError, BotoCoreError, KeyError, json.JSONDecodeError) as exc:
        raise BedrockInvocationError(str(exc)) from exc
