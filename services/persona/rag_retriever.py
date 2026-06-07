from __future__ import annotations

import os

from rag.embedding_client import embed_text
from rag.vector_store import search


def _static_fallback(question: str) -> list[dict]:
    question_l = question.lower()
    snippets = []
    if "bedrock" in question_l or "ai" in question_l:
        snippets.append({
            "source": "ai-platform-principles.md",
            "text": "Managed AI platforms are preferred where governance, auditability, and integration with existing cloud controls are important.",
            "score": 0.86,
        })
    if "3 weeks" in question_l or "timeline" in question_l or "deliver" in question_l:
        snippets.append({
            "source": "delivery-risk-standard.md",
            "text": "Delivery commitments must be validated against scope, dependencies, data migration, testing, security review, and environment readiness.",
            "score": 0.91,
        })
    if not snippets:
        snippets.append({
            "source": "default-architecture-principles.md",
            "text": "Recommendations should be grounded in approved documents and should avoid making commitments where evidence is weak.",
            "score": 0.65,
        })
    return snippets


def retrieve_context(question: str, persona_id: str, top_k: int | None = None) -> list[dict]:
    """Retrieve RAG context from vector backend, with a deterministic MVP fallback."""
    top_k = top_k or int(os.environ.get("RAG_TOP_K", "5"))
    try:
        q_embedding = embed_text(question)
        results = search(persona_id=persona_id, query_embedding=q_embedding, top_k=top_k)
        if results:
            return results
    except Exception as exc:
        print(f"RAG retrieval failed; using static fallback: {exc}")
    return _static_fallback(question)
