import json
import os
from functools import lru_cache
from pathlib import Path

import boto3


@lru_cache(maxsize=16)
def load_persona(persona_id: str) -> dict:
    """Load persona from DynamoDB, with local JSON fallback for development."""
    table_name = os.environ.get("PERSONA_TABLE")
    if table_name:
        table = boto3.resource("dynamodb").Table(table_name)
        item = table.get_item(Key={"persona_id": persona_id}).get("Item")
        if item:
            return item

    local_path = Path(__file__).resolve().parents[2] / "data" / "persona" / f"{persona_id}.json"
    if local_path.exists():
        return json.loads(local_path.read_text())

    return {
        "persona_id": persona_id,
        "tone": "calm, professional, concise",
        "answer_style": "answer directly then explain the trade-off",
        "preferred_phrases": ["My view is", "The trade-off here is"],
        "avoid_phrases": ["I guarantee"],
        "escalation_triggers": ["legal", "salary", "contract", "budget approval"],
    }
