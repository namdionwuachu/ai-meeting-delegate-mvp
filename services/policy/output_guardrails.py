from __future__ import annotations

from policy.bedrock_guardrails import apply_guardrail


def check_output(text: str, source: str = "OUTPUT") -> dict:
    guardrail = apply_guardrail(text, source=source)

    if not guardrail.get("passed", True):
        return {
            "decision": "allow",
            "reason": "output_guardrail_warn_only",
            "guardrail": guardrail,
            "warning": "Output guardrail intervened, but response was allowed for MVP testing.",
        }

    return {
        "decision": "allow",
        "reason": "output_guardrail_passed",
        "guardrail": guardrail,
    }
