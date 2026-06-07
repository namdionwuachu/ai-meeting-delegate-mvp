"""Seed persona, few-shot examples and voice profile into deployed DynamoDB tables.

Usage:
  export STACK_NAME=AIDelegateMvpStack
  export PERSONA_TABLE=<output PersonaTableName>
  export EXAMPLES_TABLE=<output StyleExamplesTableName>
  export VOICE_TABLE=<output VoiceProfilesTableName>
  export ELEVENLABS_VOICE_ID=<your ElevenLabs cloned voice id>
  python scripts/seed_aws_data.py
"""
import json
import os
import uuid
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]


def put_persona():
    table = boto3.resource("dynamodb").Table(os.environ["PERSONA_TABLE"])
    item = json.loads((ROOT / "data" / "persona" / "namdi.json").read_text())
    item.setdefault("persona_id", "namdi")
    table.put_item(Item=item)
    print(f"Seeded persona: {item['persona_id']}")


def put_examples():
    table = boto3.resource("dynamodb").Table(os.environ["EXAMPLES_TABLE"])
    path = ROOT / "data" / "examples" / "style_examples.jsonl"
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        item.setdefault("example_id", str(uuid.uuid4()))
        table.put_item(Item=item)
        print(f"Seeded example: {item['example_id']}")


def put_voice_profile():
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
    if not voice_id:
        print("Skipping voice profile: ELEVENLABS_VOICE_ID not set")
        return
    table = boto3.resource("dynamodb").Table(os.environ["VOICE_TABLE"])
    item = {
        "voice_profile_id": "namdi-v1",
        "persona_id": "namdi",
        "provider": "elevenlabs",
        "voice_id": voice_id,
        "status": "active",
        "fallback_provider": "polly",
        "fallback_voice": "Amy",
    }
    table.put_item(Item=item)
    print(f"Seeded voice profile: {item['voice_profile_id']}")


if __name__ == "__main__":
    put_persona()
    put_examples()
    put_voice_profile()
