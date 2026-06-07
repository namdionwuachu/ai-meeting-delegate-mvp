import json
import os
import uuid
from datetime import datetime, timezone

import boto3


def write_audit_record(record: dict) -> dict:
    bucket = os.environ.get("AUDIT_BUCKET")
    key = f"audit/{record.get('meeting_id', 'unknown')}/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{uuid.uuid4()}.json"
    if not bucket:
        print("AUDIT", json.dumps(record, default=str))
        return {"mode": "stdout"}
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(record, default=str).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
    return {"s3_uri": f"s3://{bucket}/{key}"}
