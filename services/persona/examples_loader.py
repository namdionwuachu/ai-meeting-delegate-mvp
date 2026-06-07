import json
import os
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key


def load_examples(persona_id: str, intent: str, limit: int = 3) -> list[dict]:
    """Load few-shot style examples. DynamoDB in AWS, local JSONL in development."""
    table_name = os.environ.get("EXAMPLES_TABLE")
    if table_name:
        table = boto3.resource("dynamodb").Table(table_name)
        try:
            resp = table.query(
                IndexName="IntentIndex",
                KeyConditionExpression=Key("intent").eq(intent) & Key("persona_id").eq(persona_id),
                Limit=limit,
            )
            if resp.get("Items"):
                return resp["Items"]
        except Exception as exc:
            print(f"Example query failed, using fallback: {exc}")

    path = Path(__file__).resolve().parents[2] / "data" / "examples" / "style_examples.jsonl"
    examples = []
    if path.exists():
        for line in path.read_text().splitlines():
            item = json.loads(line)
            if item.get("persona_id") == persona_id and item.get("intent") in [intent, "general"]:
                examples.append(item)
    return examples[:limit]
