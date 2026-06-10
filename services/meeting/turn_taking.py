"""VAD/turn-taking primitives for the meeting delegate.

This module is a local decision helper. Real audio VAD happens in the meeting provider,
WebRTC stack, or streaming media process.
"""
from __future__ import annotations

import re

DEFAULT_SILENCE_GAP_MS = 800


def is_addressed_to_delegate(transcript: str, owner_names: list[str] | None = None) -> bool:
    text = transcript or ""
    names = owner_names or ["namdi", "delegate", "ai delegate", "assistant"]
    return any(re.search(rf"\b{name}\b", text, re.I) for name in names)


def should_respond(transcript: str, silence_gap_ms: int = DEFAULT_SILENCE_GAP_MS) -> dict:
    addressed = is_addressed_to_delegate(transcript)
    return {
        "respond": addressed and silence_gap_ms >= DEFAULT_SILENCE_GAP_MS,
        "addressed_to_delegate": addressed,
        "silence_gap_ms": silence_gap_ms,
        "interruptible": True,
    }


def disclosure_message(owner_name: str) -> str:
    return (
        f"Hello everyone — I am an AI delegate joining on behalf of {owner_name}. "
        "I can answer approved questions and share context, and I will flag anything "
        "that needs direct human input."
    )
