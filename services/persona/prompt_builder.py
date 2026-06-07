from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "delegate_system_prompt.txt"


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def build_delegate_prompt(question: str, persona: dict, rag_context: list[dict], examples: list[dict], policy: dict) -> str:
    system_rules = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return f"""
{system_rules}

PERSONA PROFILE:
{_compact_json(persona)}

POLICY DECISION:
{_compact_json(policy)}

GROUNDING CONTEXT — factual basis only:
{_compact_json(rag_context)}

STYLE EXAMPLES — imitate tone and structure only, not factual claims:
{_compact_json(examples)}

MEETING QUESTION:
{question}

Return a concise spoken answer in the delegate owner's style.
""".strip()
