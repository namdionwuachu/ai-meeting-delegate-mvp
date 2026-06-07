from __future__ import annotations

from policy.bedrock_guardrails import apply_guardrail


RESTRICTED_TERMS = [
    "legal advice",
    "medical advice",
    "salary",
    "termination",
    "contract approval",
    "approve this contract",
    "approve this budget",
    "fire this person",
    "dismiss this person",
]


def check_policy(text: str, source: str = "INPUT") -> dict:
    lowered = (text or "").lower()

    for term in RESTRICTED_TERMS:
        if term in lowered:
            return {
                "decision": "block",
                "reason": "restricted_topic_rule",
                "matched_term": term,
                "escalation_required": True,
                "guardrail": {
                    "configured": False,
                    "action": "LOCAL_RULE_BLOCK",
                    "passed": False,
                },
                "intent": "restricted",
            }

    guardrail = apply_guardrail(text, source=source)

    if not guardrail.get("passed", True):
        return {
            "decision": "block",
            "reason": "bedrock_guardrail_intervened",
            "guardrail": guardrail,
            "escalation_required": True,
            "intent": "restricted",
        }

    return {
        "decision": "allow",
        "reason": "policy_passed",
        "guardrail": guardrail,
        "escalation_required": False,
        "intent": "general",
    }