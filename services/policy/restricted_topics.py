"""Restricted-topic rules for the AI Meeting Delegate.

These rules run before the LLM and before voice/avatar output. They are intentionally
simple and auditable. Replace keyword matching with a classifier once you have data.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RuleMatch:
    decision: str
    reason: str
    matched_terms: list[str]
    escalation_required: bool = False


DEFAULT_BLOCK_TERMS = [
    "salary", "termination", "dismissal", "disciplinary", "fire someone",
    "legal advice", "lawsuit", "contract signature", "sign the contract",
    "approve budget", "approve spend", "purchase order", "binding commitment",
    "medical advice", "diagnosis", "patient data", "personally identifiable",
]

DEFAULT_CAUTION_TERMS = [
    "timeline", "deadline", "commit date", "go-live", "delivery date",
    "cost estimate", "budget", "commercial", "pricing", "vendor negotiation",
]


def match_restricted_topics(text: str, block_terms: Iterable[str] | None = None, caution_terms: Iterable[str] | None = None) -> RuleMatch:
    normalized = (text or "").lower()
    block_terms = list(block_terms or DEFAULT_BLOCK_TERMS)
    caution_terms = list(caution_terms or DEFAULT_CAUTION_TERMS)

    block_hits = [term for term in block_terms if term in normalized]
    if block_hits:
        return RuleMatch(
            decision="block",
            reason="restricted_topic",
            matched_terms=block_hits,
            escalation_required=True,
        )

    caution_hits = [term for term in caution_terms if term in normalized]
    if caution_hits:
        return RuleMatch(
            decision="caution",
            reason="caution_topic",
            matched_terms=caution_hits,
            escalation_required=False,
        )

    return RuleMatch(decision="allow", reason="no_restricted_topic", matched_terms=[])
