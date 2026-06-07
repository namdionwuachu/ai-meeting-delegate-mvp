"""Ingest local sample docs into the deployed RAG store.

Usage:
  export RAG_INGEST_URL=https://.../prod/rag/ingest
  python scripts/ingest_sample_docs.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.rag.redaction import redact_sensitive_text  # noqa: E402


def post_json(url: str, payload: dict) -> dict:
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def main():
    url = os.environ["RAG_INGEST_URL"]
    docs_dir = ROOT / "data" / "docs"

    for path in docs_dir.glob("*.md"):
        raw_text = path.read_text(encoding="utf-8")
        redacted_text = redact_sensitive_text(raw_text)

        payload = {
            "persona_id": "namdi",
            "source": path.name,
            "text": redacted_text,
            "metadata": {
                "kind": "seed_doc",
                "path": str(path.relative_to(ROOT)),
                "redacted": True,
            },
        }

        print(path.name, post_json(url, payload))


if __name__ == "__main__":
    main()