from __future__ import annotations

import json
import math
import os
import uuid
from datetime import datetime, timezone
from urllib import request, error

import boto3

from rag.s3_vectors_client import put_chunks_s3_vectors, query_s3_vectors


INDEX_PREFIX = os.environ.get("RAG_INDEX_PREFIX", "rag-index")
VECTOR_BACKEND = os.environ.get("VECTOR_BACKEND", "s3_vectors")  # s3_vectors | s3_json | opensearch
OPENSEARCH_ENDPOINT = os.environ.get("OPENSEARCH_ENDPOINT", "")
OPENSEARCH_INDEX = os.environ.get("OPENSEARCH_INDEX", "ai-delegate-rag")


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(a[i] * a[i] for i in range(n))) or 1.0
    nb = math.sqrt(sum(b[i] * b[i] for i in range(n))) or 1.0
    return dot / (na * nb)


def put_chunks_s3_json(chunks: list[dict]) -> dict:
    bucket = os.environ["DOCS_BUCKET"]
    s3 = boto3.client("s3")
    written = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id") or str(uuid.uuid4())
        chunk["chunk_id"] = chunk_id
        chunk["created_at"] = chunk.get("created_at") or datetime.now(timezone.utc).isoformat()
        key = f"{INDEX_PREFIX}/{chunk['persona_id']}/{chunk_id}.json"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(chunk, default=str).encode("utf-8"),
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
        written.append({"chunk_id": chunk_id, "s3_key": key})
    return {"backend": "s3_json", "written": written}


def search_s3_json(persona_id: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
    bucket = os.environ.get("DOCS_BUCKET")
    if not bucket:
        return []
    s3 = boto3.client("s3")
    prefix = f"{INDEX_PREFIX}/{persona_id}/"
    paginator = s3.get_paginator("list_objects_v2")
    scored = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if not obj["Key"].endswith(".json"):
                continue
            payload = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read()
            item = json.loads(payload)
            score = _cosine(query_embedding, item.get("embedding", []))
            scored.append({
                "source": item.get("source", obj["Key"]),
                "text": item.get("text", ""),
                "score": round(score, 4),
                "chunk_id": item.get("chunk_id"),
                "metadata": item.get("metadata", {}),
            })
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]


def put_chunks_opensearch(chunks: list[dict]) -> dict:
    """Minimal OpenSearch bulk indexer.

    This expects OPENSEARCH_ENDPOINT to be a signed/proxy endpoint or an endpoint with
    access controlled by network/IAM outside this dependency-free MVP. For production,
    use opensearch-py with AWS SigV4 auth in a Lambda layer.
    """
    if not OPENSEARCH_ENDPOINT:
        raise RuntimeError("OPENSEARCH_ENDPOINT is not configured")
    body_lines = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id") or str(uuid.uuid4())
        chunk["chunk_id"] = chunk_id
        body_lines.append(json.dumps({"index": {"_index": OPENSEARCH_INDEX, "_id": chunk_id}}))
        body_lines.append(json.dumps(chunk))
    body = ("\n".join(body_lines) + "\n").encode("utf-8")
    req = request.Request(
        f"{OPENSEARCH_ENDPOINT.rstrip('/')}/_bulk",
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-ndjson"},
    )
    with request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def search_opensearch(persona_id: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
    if not OPENSEARCH_ENDPOINT:
        return []
    query = {
        "size": top_k,
        "query": {
            "bool": {
                "filter": [{"term": {"persona_id": persona_id}}],
                "must": [{"knn": {"embedding": {"vector": query_embedding, "k": top_k}}}],
            }
        },
    }
    req = request.Request(
        f"{OPENSEARCH_ENDPOINT.rstrip('/')}/{OPENSEARCH_INDEX}/_search",
        data=json.dumps(query).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read())
    except error.HTTPError as exc:
        raise RuntimeError(f"OpenSearch HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore')}") from exc
    hits = payload.get("hits", {}).get("hits", [])
    return [
        {
            "source": h.get("_source", {}).get("source"),
            "text": h.get("_source", {}).get("text"),
            "score": h.get("_score"),
            "chunk_id": h.get("_id"),
            "metadata": h.get("_source", {}).get("metadata", {}),
        }
        for h in hits
    ]


def put_chunks(chunks: list[dict]) -> dict:
    if VECTOR_BACKEND == "s3_vectors":
        return put_chunks_s3_vectors(chunks)
    if VECTOR_BACKEND == "opensearch":
        return put_chunks_opensearch(chunks)
    return put_chunks_s3_json(chunks)


def search(persona_id: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
    if VECTOR_BACKEND == "s3_vectors":
        results = query_s3_vectors(persona_id=persona_id, query_embedding=query_embedding, top_k=top_k)
        if results:
            return results
    if VECTOR_BACKEND == "opensearch":
        results = search_opensearch(persona_id, query_embedding, top_k)
        if results:
            return results
    return search_s3_json(persona_id, query_embedding, top_k)
