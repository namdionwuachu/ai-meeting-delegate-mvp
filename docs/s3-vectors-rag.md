# S3 Vectors RAG Backend

This release replaces the default RAG backend from the MVP `s3_json` fallback/OpenSearch option to **Amazon S3 Vectors**.

## Why

S3 Vectors is a lower-operations vector store for the AI Delegate MVP. It lets the platform keep documents in S3, generate Titan embeddings, and query a vector index without provisioning OpenSearch capacity.

## Runtime flow

```text
/rag/ingest
  -> clean + chunk document
  -> Titan embedding per chunk
  -> s3vectors.put_vectors
  -> S3 Vector bucket/index

/delegate/respond
  -> Titan embedding for question
  -> s3vectors.query_vectors filtered by persona_id
  -> Bedrock answer generation
```

## New environment variables

```text
VECTOR_BACKEND=s3_vectors
S3_VECTOR_BUCKET_NAME=<your-vector-bucket>
S3_VECTOR_INDEX_NAME=ai-delegate-rag
S3_VECTORS_BATCH_SIZE=50
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
EMBEDDING_DIMENSIONS=1024
```

## Create the vector bucket and index

After `cdk deploy`, use the CDK output `S3VectorBucketName` and run:

```bash
python scripts/setup_s3_vectors.py \
  --vector-bucket <S3VectorBucketName> \
  --index ai-delegate-rag \
  --dimension 1024 \
  --region eu-west-2
```

Use the same region as the deployed Lambda/Bedrock stack.

## Ingest documents

```bash
python scripts/ingest_sample_docs.py
```

Or call the API:

```bash
curl -X POST "$API_URL/rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "namdi",
    "source": "architecture-decision.md",
    "text": "Managed services are preferred where governance and auditability matter."
  }'
```

## Fallback modes

If you need a local-only demo without S3 Vectors, set:

```text
VECTOR_BACKEND=s3_json
```

If you later need high-query enterprise retrieval, the old OpenSearch adapter remains available:

```text
VECTOR_BACKEND=opensearch
OPENSEARCH_ENDPOINT=<endpoint>
OPENSEARCH_INDEX=ai-delegate-rag
```
