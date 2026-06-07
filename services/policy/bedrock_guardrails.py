"""Bedrock Guardrails adapter.

Uses the independent ApplyGuardrail API when BEDROCK_GUARDRAIL_ID and
BEDROCK_GUARDRAIL_VERSION are provided directly or via SSM Parameter Store.
If not configured, it returns a pass result so local demos still work.
"""
from __future__ import annotations

import os
from typing import Any
import boto3

try:
    from shared_ssm import get_env_or_parameter
except Exception:  # pragma: no cover
    from services.shared_ssm import get_env_or_parameter

_runtime = None


def _client():
    global _runtime
    if _runtime is None:
        _runtime = boto3.client("bedrock-runtime")
    return _runtime


def apply_guardrail(text: str, source: str = "INPUT") -> dict[str, Any]:
    guardrail_id = get_env_or_parameter("BEDROCK_GUARDRAIL_ID", "BEDROCK_GUARDRAIL_ID_PARAM")
    guardrail_version = get_env_or_parameter("BEDROCK_GUARDRAIL_VERSION", "BEDROCK_GUARDRAIL_VERSION_PARAM")
    if not guardrail_id or not guardrail_version:
        return {"configured": False, "action": "NONE", "passed": True, "reason": "guardrail_not_configured"}

    response = _client().apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=guardrail_version,
        source=source,
        content=[{"text": {"text": text or ""}}],
    )
    action = response.get("action", "NONE")
    return {
        "configured": True,
        "action": action,
        "passed": action == "NONE",
        "outputs": response.get("outputs", []),
        "assessments": response.get("assessments", []),
        "usage": response.get("usage", {}),
    }
