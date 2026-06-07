#!/usr/bin/env python3
from __future__ import annotations

"""Create the S3 Vector bucket and index used by the RAG layer.

Run after `cdk deploy` because CDK outputs the recommended names but, at time of
writing, S3 Vectors is managed through the s3vectors API rather than normal S3
bucket constructs in this MVP.

Example:
  python scripts/setup_s3_vectors.py \
    --vector-bucket ai-delegate-vectors \
    --index ai-delegate-rag \
    --dimension 1024 \
    --region eu-west-2
"""

import argparse
import time

import boto3
from botocore.exceptions import ClientError


def exists_vector_bucket(client, name: str) -> bool:
    try:
        client.get_vector_bucket(vectorBucketName=name)
        return True
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"NotFoundException", "NoSuchVectorBucket", "ResourceNotFoundException"}:
            return False
        raise


def exists_index(client, vector_bucket: str, index: str) -> bool:
    try:
        client.get_index(vectorBucketName=vector_bucket, indexName=index)
        return True
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"NotFoundException", "NoSuchIndex", "ResourceNotFoundException"}:
            return False
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vector-bucket", required=True)
    parser.add_argument("--index", default="ai-delegate-rag")
    parser.add_argument("--dimension", type=int, default=1024)
    parser.add_argument("--region", default=None)
    parser.add_argument("--distance-metric", default="cosine", choices=["cosine", "euclidean"])
    args = parser.parse_args()

    client = boto3.client("s3vectors", region_name=args.region)

    if exists_vector_bucket(client, args.vector_bucket):
        print(f"Vector bucket already exists: {args.vector_bucket}")
    else:
        print(f"Creating vector bucket: {args.vector_bucket}")
        client.create_vector_bucket(
            vectorBucketName=args.vector_bucket,
            encryptionConfiguration={"sseType": "AES256"},
            tags={"Application": "ai-meeting-delegate", "Purpose": "rag"},
        )

    # Give the control plane a small moment before creating the index.
    time.sleep(2)

    if exists_index(client, args.vector_bucket, args.index):
        print(f"Vector index already exists: {args.index}")
    else:
        print(f"Creating vector index: {args.index}")
        client.create_index(
            vectorBucketName=args.vector_bucket,
            indexName=args.index,
            dataType="float32",
            dimension=args.dimension,
            distanceMetric=args.distance_metric,
            metadataConfiguration={
                # Keep large text as non-filterable reference metadata; filter on persona_id/source/etc.
                "nonFilterableMetadataKeys": ["source_text"]
            },
            tags={"Application": "ai-meeting-delegate", "Purpose": "rag"},
        )

    print("Done.")
    print(f"S3_VECTOR_BUCKET_NAME={args.vector_bucket}")
    print(f"S3_VECTOR_INDEX_NAME={args.index}")


if __name__ == "__main__":
    main()
