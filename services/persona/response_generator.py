from __future__ import annotations

from persona.bedrock_client import BedrockInvocationError, invoke_bedrock
from persona.prompt_builder import build_delegate_prompt
from persona.token_budget import check_token_budget
from persona.model_config import get_model_config


def generate_delegate_response(question: str, persona: dict, rag_context: list[dict], examples: list[dict], policy: dict) -> dict:
    prompt = build_delegate_prompt(question, persona, rag_context, examples, policy)
    cfg = get_model_config()
    budget = check_token_budget(prompt, cfg.max_tokens)

    try:
        result = invoke_bedrock(prompt)
        return {
            "text": result["text"],
            "model_id": result["model_id"],
            "latency_ms": result["latency_ms"],
            "usage": result.get("usage", {}),
            "budget": result.get("budget", budget.__dict__),
            "fallback": False,
        }
    except BedrockInvocationError as exc:
        print(f"Bedrock invocation failed, returning deterministic fallback: {exc}")
        phrase = persona.get("preferred_phrases", ["My view is"])[0]
        if policy.get("intent") == "timeline_commitment":
            text = f"{phrase} we should be careful committing to that timeline. The right next step is to validate the scope, dependencies, testing and governance path before confirming a date."
        else:
            text = f"{phrase} I would answer this cautiously and ground the response in the approved project context before making a commitment."
        return {
            "text": text,
            "model_id": cfg.model_id,
            "latency_ms": None,
            "usage": {},
            "budget": budget.__dict__,
            "fallback": True,
            "fallback_reason": str(exc),
        }
