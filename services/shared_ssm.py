from __future__ import annotations

import os
from functools import lru_cache

import boto3


@lru_cache(maxsize=64)
def get_parameter(name: str | None, default: str | None = None, with_decryption: bool = True) -> str | None:
    """Read a value from AWS Systems Manager Parameter Store.

    Use SecureString for API keys and WithDecryption=True. Values are cached for
    the lifetime of a warm Lambda container to avoid repeated SSM calls.
    """
    if not name:
        return default
    try:
        return boto3.client("ssm").get_parameter(Name=name, WithDecryption=with_decryption)["Parameter"]["Value"]
    except Exception:
        return default


def get_env_or_parameter(env_name: str, param_env_name: str, default: str | None = None) -> str | None:
    """Prefer a direct env var for local dev, otherwise read the SSM path held in another env var."""
    direct = os.environ.get(env_name)
    if direct:
        return direct
    return get_parameter(os.environ.get(param_env_name), default=default)
