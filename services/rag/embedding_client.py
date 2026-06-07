from __future__ import annotations

import json
import os
import hashlib
import random
from typing import List

import boto3


EMBEDDING_MODEL_ID = os.environ.get("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "1024"))


def _deterministic_local_embedding(text: str, dims: int = EMBEDDING_DIMENSIONS) -> list[float]:
    """Local fallback so tests run without AWS. Not for production retrieval quality."""
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    vector = [rng.uniform(-1.0, 1.0) for _ in range(dims)]
    norm = sum(v * v for v in vector) ** 0.5 or 1.0
    return [round(v / norm, 8) for v in vector]


def embed_text(text: str) -> list[float]:
    if os.environ.get("LOCAL_MODE", "false").lower() == "true":
        return _deterministic_local_embedding(text)

    client = boto3.client("bedrock-runtime")
    body = {
        "inputText": text,
        "dimensions": EMBEDDING_DIMENSIONS,
        "normalize": True,
    }
    response = client.invoke_model(modelId=EMBEDDING_MODEL_ID, body=json.dumps(body))
    payload = json.loads(response["body"].read())
    embedding = payload.get("embedding")
    if not embedding:
        raise RuntimeError(f"Embedding model returned no embedding: {payload}")
    return embedding
