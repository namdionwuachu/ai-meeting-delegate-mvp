"""Bedrock model configuration for the AI Meeting Delegate.

Supports Claude 3 Haiku/Sonnet/Opus style message API models on Amazon Bedrock.
Configuration is driven by environment variables so you can tune by environment
without changing code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BedrockModelConfig:
    model_id: str
    max_tokens: int
    temperature: float
    top_p: float
    anthropic_version: str = "bedrock-2023-05-31"
    read_timeout_seconds: int = 20
    connect_timeout_seconds: int = 5


def get_model_config() -> BedrockModelConfig:
    return BedrockModelConfig(
        model_id=os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
        max_tokens=int(os.environ.get("BEDROCK_MAX_TOKENS", "450")),
        temperature=float(os.environ.get("BEDROCK_TEMPERATURE", "0.3")),
        top_p=float(os.environ.get("BEDROCK_TOP_P", "0.9")),
        read_timeout_seconds=int(os.environ.get("BEDROCK_READ_TIMEOUT_SECONDS", "20")),
        connect_timeout_seconds=int(os.environ.get("BEDROCK_CONNECT_TIMEOUT_SECONDS", "5")),
    )


MODEL_PROFILES = {
    "haiku_fast": {
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "use_case": "Lowest-latency meeting responses and cheap MVP testing",
    },
    "sonnet_balanced": {
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "use_case": "Better reasoning for architecture and stakeholder questions",
    },
    "sonnet_35_balanced": {
        "model_id": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "use_case": "Higher quality responses where the model is enabled in your Bedrock region",
    },
}
