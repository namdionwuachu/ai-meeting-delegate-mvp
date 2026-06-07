from __future__ import annotations

from voice.elevenlabs_client import synthesize_with_elevenlabs
from voice.polly_fallback import synthesize_with_polly


def synthesize_voice(text: str, voice_profile_id: str, meeting_id: str, output_mode: str = "file") -> dict:
    """Try ElevenLabs first, fall back to Polly."""
    try:
        result = synthesize_with_elevenlabs(
            text=text,
            voice_profile_id=voice_profile_id,
            meeting_id=meeting_id,
            output_mode=output_mode,
        )
        result["fallback_used"] = False
        return result
    except Exception as exc:
        print(f"ElevenLabs failed; using Polly fallback: {exc}")
        result = synthesize_with_polly(text=text, meeting_id=meeting_id)
        result["fallback_used"] = True
        result["fallback_reason"] = str(exc)
        return result
