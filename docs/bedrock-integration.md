# Real Bedrock Integration

This version adds the production Bedrock response path for the Persona Engine.

## Files added

- `services/persona/model_config.py` — model selection and runtime tuning from ENV.
- `services/persona/token_budget.py` — lightweight prompt-token and per-response cost controls.
- `services/persona/prompt_builder.py` — prompt composition using persona, RAG context, examples and policy.
- `services/persona/prompts/delegate_system_prompt.txt` — reusable system instructions.
- `services/persona/bedrock_client.py` — real `bedrock-runtime.invoke_model` call using Anthropic Claude Messages API format.

## Default model

The CDK stack defaults to:

```text
anthropic.claude-3-haiku-20240307-v1:0
```

This is intentionally set as the MVP default because it is lower latency and lower cost for meeting-style responses. For deeper architecture reasoning, change `BEDROCK_MODEL_ID` to Sonnet in the CDK environment or Lambda configuration.

## Environment variables

```text
BEDROCK_MODEL_ID
BEDROCK_MAX_TOKENS
BEDROCK_TEMPERATURE
BEDROCK_TOP_P
BEDROCK_READ_TIMEOUT_SECONDS
BEDROCK_CONNECT_TIMEOUT_SECONDS
MAX_PROMPT_TOKENS
MAX_COST_PER_RESPONSE_USD
BEDROCK_INPUT_COST_PER_1K
BEDROCK_OUTPUT_COST_PER_1K
```

## Runtime flow

```text
/delegate/respond
→ policy check
→ load persona
→ retrieve RAG context
→ load few-shot examples
→ build prompt
→ token/cost budget check
→ Bedrock invoke_model
→ return text + usage metadata
→ optional voice synthesis
→ audit log
```

## Notes

The token estimator is deliberately lightweight to keep the Lambda small. Replace `estimate_tokens()` with a tokenizer or use CloudWatch/Bedrock usage metrics for production-grade billing reconciliation.
