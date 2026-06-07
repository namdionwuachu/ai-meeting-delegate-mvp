def score_confidence(rag_context: list[dict], examples: list[dict], policy: dict) -> float:
    score = 0.45
    if rag_context:
        score += min(max(rag_context[0].get("score", 0.5), 0), 1) * 0.3
    if examples:
        score += 0.15
    if policy.get("risk") == "medium":
        score -= 0.1
    if policy.get("decision") == "block":
        return 0.0
    return round(max(0.0, min(score, 0.95)), 2)
