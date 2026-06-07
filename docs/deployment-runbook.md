# Deployment Runbook — AI Meeting Delegate MVP

This build wires the infrastructure layer for the MVP:

- API Gateway
- Delegate Orchestrator Lambda
- Voice Service Lambda
- DynamoDB tables: persona, style examples, voice profiles, meeting sessions
- S3 buckets: documents, audit, generated audio
- SSM Parameter Store: ElevenLabs API key and optional Bedrock guardrail config
- IAM permissions for Bedrock, Polly, DynamoDB, S3, SSM Parameter Store, SNS and X-Ray
- CloudWatch log retention and basic Lambda alarms

## 1. Deploy

```bash
cd infrastructure/cdk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap
cdk deploy
```

## 2. Store the ElevenLabs API key

Use the `ElevenLabsParameterName` output from the stack:

```bash
aws parametersmanager put-parameter-value \
  --parameter-id /AIDelegateMvpStack/elevenlabs/api-key \
  --value 'YOUR_ELEVENLABS_API_KEY'
```

## 3. Seed persona, examples and voice profile

```bash
export PERSONA_TABLE=<PersonaTableName output>
export EXAMPLES_TABLE=<StyleExamplesTableName output>
export VOICE_TABLE=<VoiceProfilesTableName output>
export ELEVENLABS_VOICE_ID=<your ElevenLabs voice_id>
python scripts/seed_aws_data.py
```

## 4. Test text response

```bash
curl -X POST '<DelegateRespondUrl output>' \
  -H 'Content-Type: application/json' \
  -d '{
    "persona_id":"namdi",
    "meeting_id":"demo-001",
    "mode":"text",
    "transcript":"Namdi, can we deliver this platform in 3 weeks?"
  }'
```

## 5. Test voice response

```bash
curl -X POST '<VoiceSpeakUrl output>' \
  -H 'Content-Type: application/json' \
  -d '{
    "voice_profile_id":"namdi-v1",
    "meeting_id":"demo-001",
    "text":"My view is we should validate the scope before committing."
  }'
```

The response returns an S3 URI for the generated MP3. If ElevenLabs is not configured, the code falls back to AWS Polly.

## 6. Next wiring

The next build step is to add true RAG retrieval:

- S3 document upload
- embedding generation
- OpenSearch Serverless or S3 Vectors index
- replacement of `services/persona/rag_retriever.py`



## Configure S3 Vectors for RAG

This package uses S3 Vectors by default instead of OpenSearch. After `cdk deploy`, copy the `S3VectorBucketName` output and create the vector bucket/index:

```bash
python scripts/setup_s3_vectors.py \
  --vector-bucket <S3VectorBucketName> \
  --index ai-delegate-rag \
  --dimension 1024 \
  --region <your-region>
```

Then load persona/examples and ingest documents:

```bash
python scripts/seed_aws_data.py
python scripts/ingest_sample_docs.py
```

The Lambda environment defaults are:

```text
VECTOR_BACKEND=s3_vectors
S3_VECTOR_INDEX_NAME=ai-delegate-rag
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
EMBEDDING_DIMENSIONS=1024
```

## Parameter Store update

This version does **not** require AWS Secrets Manager.

After `cdk deploy`, store runtime credentials using:

```bash
export AWS_REGION=eu-west-2
export ELEVENLABS_API_KEY='your-key'
export ELEVENLABS_VOICE_ID='your-voice-id'
./scripts/setup_ssm_parameters.sh AIDelegateStack
```

Add Recall.ai, HeyGen and D-ID parameters only when you are ready to test the meeting and avatar layers.
