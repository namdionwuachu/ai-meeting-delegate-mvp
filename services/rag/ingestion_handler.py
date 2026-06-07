from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime, timezone

import boto3

from rag.chunker import clean_text, chunk_text
from rag.embedding_client import embed_text
from rag.vector_store import put_chunks


def _response(status_code: int, body: dict):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body),
    }


def _read_text_from_s3(s3_uri: str) -> tuple[str, str]:
    if not s3_uri.startswith("s3://"):
        raise ValueError("s3_uri must start with s3://")
    bucket_key = s3_uri[5:]
    bucket, key = bucket_key.split("/", 1)
    obj = boto3.client("s3").get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8", errors="replace"), key


def handler(event, context):
    """POST /rag/ingest

    Body options:
      {"persona_id":"namdi", "text":"...", "source":"..."}
      {"persona_id":"namdi", "s3_uri":"s3://bucket/key.txt"}
    """
    try:
        body = json.loads(event.get("body") or "{}") if "body" in event else event
        persona_id = body.get("persona_id", "namdi")
        source = body.get("source") or body.get("s3_uri") or "inline-upload"

        text = body.get("text")
        if body.get("s3_uri") and not text:
            text, source_key = _read_text_from_s3(body["s3_uri"])
            source = source_key
        if not text:
            return _response(400, {"error": "text or s3_uri is required"})

        text = clean_text(text)
        max_chars = int(body.get("max_chars", os.environ.get("RAG_CHUNK_MAX_CHARS", "1800")))
        chunks_raw = chunk_text(text, max_chars=max_chars)
        document_id = body.get("document_id") or str(uuid.uuid4())
        chunks = []
        for idx, chunk in enumerate(chunks_raw):
            chunks.append({
                "persona_id": persona_id,
                "document_id": document_id,
                "chunk_id": f"{document_id}-{idx:04d}",
                "source": source,
                "text": chunk,
                "embedding": embed_text(chunk),
                "metadata": body.get("metadata", {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        write_result = put_chunks(chunks)
        # Store cleaned source as a durable doc object too.
        docs_bucket = os.environ.get("DOCS_BUCKET")
        if docs_bucket:
            boto3.client("s3").put_object(
                Bucket=docs_bucket,
                Key=f"raw/{persona_id}/{document_id}.txt",
                Body=text.encode("utf-8"),
                ContentType="text/plain",
                ServerSideEncryption="AES256",
            )
        return _response(200, {
            "status": "ingested",
            "persona_id": persona_id,
            "document_id": document_id,
            "chunks": len(chunks),
            "write_result": write_result,
        })
    except Exception as exc:
        return _response(500, {"error": str(exc)})
