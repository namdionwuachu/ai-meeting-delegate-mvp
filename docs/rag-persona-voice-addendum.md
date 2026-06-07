# Addendum: RAG Ingestion, Persona Seeding and ElevenLabs Voice

This addendum extends the MVP with three production slices:

1. RAG ingestion and retrieval
2. Persona/few-shot/voice-profile loading
3. ElevenLabs `/voice/speak` with Polly fallback

## New API routes

- `POST /rag/ingest` — ingest inline text or an S3 text object into the RAG store.
- `POST /seed/persona` — seed persona JSON, few-shot examples and an optional voice profile.
- `POST /voice/speak` — synthesize speech using ElevenLabs first, then Polly fallback.

## RAG backend modes

The MVP defaults to `VECTOR_BACKEND=s3_json`. This stores chunk JSON files with embeddings under:

```text
s3://<DOCS_BUCKET>/rag-index/<persona_id>/<chunk_id>.json
```

This is simple, cheap and good for early testing. For production, set:

```text
VECTOR_BACKEND=opensearch
OPENSEARCH_ENDPOINT=https://<your-opensearch-endpoint>
OPENSEARCH_INDEX=ai-delegate-rag
```

and use the OpenSearch mapping in `docs/opensearch-index-mapping.json`.

## Ingest request

```json
{
  "persona_id": "namdi",
  "source": "ai-platform-principles.md",
  "text": "Managed AI platforms are preferred...",
  "metadata": {"kind": "architecture_standard"}
}
```

or:

```json
{
  "persona_id": "namdi",
  "s3_uri": "s3://my-bucket/my-doc.txt"
}
```

The ingestion function cleans text, chunks it, calls Titan Embeddings on Bedrock, and writes the vector records to the configured vector backend.

## Persona seed request

```json
{
  "persona": {
    "persona_id": "namdi",
    "tone": "calm, strategic, direct",
    "answer_style": "recommendation first, then rationale"
  },
  "examples": [
    {
      "persona_id": "namdi",
      "example_id": "ex-001",
      "intent": "architecture_tradeoff",
      "question": "Should we build or buy?",
      "answer": "My view is we should lean towards managed services unless control is critical."
    }
  ],
  "voice_profile": {
    "voice_profile_id": "namdi-v1",
    "persona_id": "namdi",
    "provider": "elevenlabs",
    "voice_id": "YOUR_ELEVENLABS_VOICE_ID",
    "model_id": "eleven_turbo_v2_5",
    "stability": "0.75",
    "similarity_boost": "0.85",
    "fallback_provider": "polly",
    "fallback_voice": "Amy"
  }
}
```

## Voice request

```json
{
  "voice_profile_id": "namdi-v1",
  "meeting_id": "demo-001",
  "text": "My view is we should validate the scope before committing.",
  "output_mode": "stream"
}
```

The Lambda uses the ElevenLabs streaming endpoint when `output_mode` is `stream` or `streaming`, writes the MP3 to S3, and returns a presigned URL. For live meeting injection, replace the S3 write loop with direct chunk forwarding to your WebRTC/Recall.ai media bridge.

## Deployment order

1. Deploy CDK.
2. Store the ElevenLabs API key in the generated SSM Parameter Store parameter.
3. Seed persona and examples with `scripts/seed_aws_data.py` or `POST /seed/persona`.
4. Ingest docs with `scripts/ingest_sample_docs.py` or `POST /rag/ingest`.
5. Test `/delegate/respond` with `mode=voice`.
