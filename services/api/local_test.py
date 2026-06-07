import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from orchestrator.lambda_handler import handler

os.environ.setdefault("AUDIT_BUCKET", "")
os.environ.setdefault("AUDIO_BUCKET", "")

if __name__ == "__main__":
    event = {
        "meeting_id": "demo-001",
        "persona_id": "namdi",
        "transcript": "Namdi, can we deliver the new AI platform in 3 weeks?",
        "mode": "text"
    }
    print(json.dumps(handler(event, None), indent=2))
