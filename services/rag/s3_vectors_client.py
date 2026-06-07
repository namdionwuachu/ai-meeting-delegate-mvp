from __future__ import annotations

"""S3 Vectors backend for the AI Meeting Delegate RAG layer.

This module intentionally wraps boto3's `s3vectors` client behind a small
interface so the rest of the app can switch between:
- s3_vectors  -> production MVP backend
- s3_json     -> local/demo fallback
- opensearch  -> optional enterprise backend later

Expected vector shape for S3 Vectors:
{
  "key": "document-id-0001",
  "data": {"float32": [0.1, ...]},
  "metadata": {"persona_id": "namdi", "source_text": "...", ...}
}
"""

import os
from typing import Any

import boto3
from botocore.exceptions import ClientError


DEFAULT_VECTOR_BUCKET = os.environ.get("S3_VECTOR_BUCKET_NAME", "")
DEFAULT_VECTOR_INDEX = os.environ.get("S3_VECTOR_INDEX_NAME", "ai-delegate-rag")
DEFAULT_TOP_K = int(os.environ.get("RAG_TOP_K", "5"))


def _client():
    return boto3.client("s3vectors")


def _vector_bucket_name() -> str:
    name = os.environ.get("S3_VECTOR_BUCKET_NAME") or DEFAULT_VECTOR_BUCKET
    if not name:
        raise RuntimeError("S3_VECTOR_BUCKET_NAME is not configured")
    return name


def _index_name() -> str:
    return os.environ.get("S3_VECTOR_INDEX_NAME") or DEFAULT_VECTOR_INDEX


def _metadata_for_vector(chunk: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(chunk.get("metadata") or {})
    metadata.update(
        {
            "persona_id": chunk.get("persona_id", "namdi"),
            "document_id": chunk.get("document_id", ""),
            "chunk_id": chunk.get("chunk_id", ""),
            "source": chunk.get("source", ""),
            # Store source_text as non-filterable metadata in the index config.
            # This keeps retrieval simple without a second object lookup.
            "source_text": chunk.get("text", ""),
            "created_at": chunk.get("created_at", ""),
        }
    )
    return metadata


def put_chunks_s3_vectors(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Insert chunk embeddings into an S3 Vector index.

    Batches are kept small to avoid large request payloads because text chunks are
    stored in metadata. If you store large chunks, reduce batch_size or store text
    in S3 and keep only an S3 pointer in metadata.
    """
    if not chunks:
        return {"backend": "s3_vectors", "written": []}

    s3v = _client()
    vector_bucket_name = _vector_bucket_name()
    index_name = _index_name()
    batch_size = int(os.environ.get("S3_VECTORS_BATCH_SIZE", "50"))
    written: list[dict[str, str]] = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vectors = []
        for chunk in batch:
            key = chunk.get("chunk_id")
            if not key:
                raise ValueError("chunk_id is required for S3 Vectors")
            embedding = chunk.get("embedding") or []
            if not embedding:
                raise ValueError(f"embedding missing for chunk_id={key}")
            vectors.append(
                {
                    "key": key,
                    "data": {"float32": [float(x) for x in embedding]},
                    "metadata": _metadata_for_vector(chunk),
                }
            )

        # The public boto3 API uses vectorBucketName/indexName/vectors.
        s3v.put_vectors(
            vectorBucketName=vector_bucket_name,
            indexName=index_name,
            vectors=vectors,
        )
        written.extend({"chunk_id": v["key"], "vector_bucket": vector_bucket_name, "index": index_name} for v in vectors)

    return {"backend": "s3_vectors", "written": written, "count": len(written)}


def query_s3_vectors(
    persona_id: str,
    query_embedding: list[float],
    top_k: int | None = None,
    metadata_filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Query an S3 Vector index and return RAG-style context chunks."""
    if not query_embedding:
        return []

    s3v = _client()
    top_k = top_k or DEFAULT_TOP_K
    vector_bucket_name = _vector_bucket_name()
    index_name = _index_name()

    # S3 Vectors supports metadata filtering. We always scope by persona_id so
    # one vector index can safely hold multiple delegate/persona corpora.
    filter_expr: dict[str, Any] = {"persona_id": persona_id}
    if metadata_filter:
        filter_expr.update(metadata_filter)

    try:
        response = s3v.query_vectors(
            vectorBucketName=vector_bucket_name,
            indexName=index_name,
            queryVector={"float32": [float(x) for x in query_embedding]},
            topK=top_k,
            filter=filter_expr,
            returnDistance=True,
            returnMetadata=True,
        )
    except ClientError as exc:
        raise RuntimeError(f"S3 Vectors query failed: {exc.response.get('Error', {}).get('Message', str(exc))}") from exc

    results = []
    for item in response.get("vectors", []):
        metadata = item.get("metadata") or {}
        distance = item.get("distance")
        # For cosine distance, lower is better. Convert to an intuitive score.
        score = None
        if distance is not None:
            try:
                score = round(1.0 - float(distance), 4)
            except Exception:
                score = distance
        results.append(
            {
                "source": metadata.get("source"),
                "text": metadata.get("source_text", ""),
                "score": score,
                "distance": distance,
                "chunk_id": metadata.get("chunk_id") or item.get("key"),
                "metadata": {k: v for k, v in metadata.items() if k != "source_text"},
            }
        )
    return results
