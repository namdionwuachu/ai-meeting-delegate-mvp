# AI Meeting Delegate MVP

This repository is the first deployable slice of the AI Meeting Delegate architecture.

It implements the first production thread:

```text
Question / Transcript
→ Policy check
→ Persona + few-shot examples
→ Bedrock response
→ optional ElevenLabs voice synthesis
→ Polly fallback
→ S3 audit log
```

The full architecture described in the production script has eight layers: Meeting, Speech, Orchestration, Persona Engine, Policy, Voice, Avatar and Audit. This MVP wires the Orchestration, Persona, Policy, Voice and Audit layers first.

## What is wired now

- API Gateway
- Delegate Orchestrator Lambda: `POST /delegate/respond`
- Voice Service Lambda: `POST /voice/speak`
- Health endpoint: `GET /health`
- DynamoDB tables
  - persona profiles
  - style examples
  - voice profiles
  - meeting sessions
- S3 buckets
  - documents
  - audit logs
  - generated audio
- SSM Parameter Store
  - ElevenLabs API key
  - optional Bedrock guardrail config placeholder
- IAM permissions
  - Bedrock InvokeModel
  - Polly SynthesizeSpeech
  - DynamoDB read/write
  - S3 read/write
  - SSM Parameter Store read
  - SNS publish
  - X-Ray tracing
- CloudWatch
  - Lambda log retention
  - Lambda error alarms
  - Lambda duration alarms

## Project structure

```text
ai-meeting-delegate-mvp/
├── infrastructure/cdk/          # AWS CDK app and stack
├── services/
│   ├── orchestrator/            # Main delegate response Lambda
│   ├── persona/                 # Persona loading, examples, RAG placeholder, Bedrock client
│   ├── policy/                  # Blocking and confidence logic
│   ├── voice/                   # ElevenLabs + Polly fallback
│   └── audit/                   # S3 audit writer
├── data/                        # Local persona and few-shot examples
├── scripts/                     # Seed scripts
└── docs/                        # Runbooks and runtime flow
```

## Deploy

See: `docs/deployment-runbook.md`.

## Important limits of this build

This is not yet the full meeting delegate. The following are intentionally left for later phases:

- live meeting bot
- WebRTC audio injection
- Amazon Transcribe streaming
- VAD / turn-taking
- real RAG vector index
- Bedrock Guardrails API integration
- HeyGen / D-ID avatar streaming

Those should be added after the text + voice MVP works reliably.

## v1.2 Bedrock integration added

This build now includes a real Amazon Bedrock integration path for the Persona Engine:

- Claude Messages API invocation through `bedrock-runtime.invoke_model`
- reusable prompt template
- Haiku/Sonnet model configuration through environment variables
- max token, temperature and top-p controls
- lightweight token and cost guardrails
- response metadata returned to the API caller and audit log

See `docs/bedrock-integration.md` for details.

## v1.3 Addendum: RAG + Persona Seed + ElevenLabs Voice

This package now includes:

- `POST /rag/ingest` for document upload/chunking/embedding into the RAG store.
- Titan embedding generation via Bedrock.
- Configurable vector backend: `s3_json` for MVP, `opensearch` for production.
- `POST /seed/persona` for persona JSON, few-shot examples and voice-profile loading.
- Real `/voice/speak` with ElevenLabs primary synthesis and Polly fallback.
- Presigned S3 audio URL output for demo playback.

See `docs/rag-persona-voice-addendum.md` for request examples and deployment order.

## vNext Addendum: Guardrails, Test UI, Meeting, Avatar

This package adds:

- Restricted-topic rules
- Bedrock Guardrails `ApplyGuardrail` integration
- SNS escalation
- Browser test UI
- Recall.ai meeting connector skeleton
- VAD/turn-taking helper
- Disclosure message helper
- HeyGen avatar adapter
- D-ID fallback adapter
- `/meeting/join` and `/avatar/speak` API routes

See:

- `docs/product-layer-addendum.md`
- `docs/meeting-avatar-roadmap.md`
- `frontend/test-ui/index.html`


## S3 Vectors RAG backend

This version defaults the RAG layer to `VECTOR_BACKEND=s3_vectors`. The app now writes chunk embeddings to an S3 Vector bucket/index via `boto3.client("s3vectors")` and queries that index at runtime.

Create the vector bucket/index after CDK deploy:

```bash
python scripts/setup_s3_vectors.py \
  --vector-bucket <S3VectorBucketName from cdk output> \
  --index ai-delegate-rag \
  --dimension 1024 \
  --region eu-west-2
```

Then ingest sample documents:

```bash
python scripts/ingest_sample_docs.py
```

See `docs/s3-vectors-rag.md` for the full setup notes.
