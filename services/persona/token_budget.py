"""Token and rough cost controls for prompt assembly.

This uses a lightweight approximation rather than provider tokenizers to keep the
Lambda package small. For production, replace estimate_tokens with a tokenizer
or Bedrock invocation metrics from CloudWatch.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class TokenBudgetResult:
    allowed: bool
    estimated_input_tokens: int
    max_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    reason: str | None = None


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    # Conservative English approximation: ~4 chars per token.
    return max(1, len(text) // 4)


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    # Defaults are rough Claude 3 Haiku Bedrock public-style rates.
    # Override these through ENV for the exact model/region/rate card you use.
    input_per_1k = float(os.environ.get("BEDROCK_INPUT_COST_PER_1K", "0.00025"))
    output_per_1k = float(os.environ.get("BEDROCK_OUTPUT_COST_PER_1K", "0.00125"))
    return round((input_tokens / 1000 * input_per_1k) + (output_tokens / 1000 * output_per_1k), 6)


def check_token_budget(prompt: str, max_output_tokens: int) -> TokenBudgetResult:
    input_tokens = estimate_tokens(prompt)
    max_input_tokens = int(os.environ.get("MAX_PROMPT_TOKENS", "6000"))
    est_cost = estimate_cost_usd(input_tokens, max_output_tokens)
    max_cost = float(os.environ.get("MAX_COST_PER_RESPONSE_USD", "0.05"))

    if input_tokens > max_input_tokens:
        return TokenBudgetResult(
            allowed=False,
            estimated_input_tokens=input_tokens,
            max_input_tokens=max_input_tokens,
            estimated_output_tokens=max_output_tokens,
            estimated_cost_usd=est_cost,
            reason="prompt_token_budget_exceeded",
        )
    if est_cost > max_cost:
        return TokenBudgetResult(
            allowed=False,
            estimated_input_tokens=input_tokens,
            max_input_tokens=max_input_tokens,
            estimated_output_tokens=max_output_tokens,
            estimated_cost_usd=est_cost,
            reason="cost_budget_exceeded",
        )
    return TokenBudgetResult(
        allowed=True,
        estimated_input_tokens=input_tokens,
        max_input_tokens=max_input_tokens,
        estimated_output_tokens=max_output_tokens,
        estimated_cost_usd=est_cost,
    )
