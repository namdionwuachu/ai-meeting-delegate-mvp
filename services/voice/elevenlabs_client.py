from __future__ import annotations

import json
import os
import uuid
from urllib import request, error

import boto3

try:
    from shared_ssm import get_env_or_parameter
except Exception:  # pragma: no cover
    from services.shared_ssm import get_env_or_parameter


def _get_api_key() -> str | None:
    return get_env_or_parameter("ELEVENLABS_API_KEY", "ELEVENLABS_API_KEY_PARAM")


def _get_default_voice_id() -> str | None:
    return get_env_or_parameter("ELEVENLABS_VOICE_ID", "ELEVENLABS_VOICE_ID_PARAM")


def _get_voice_profile(voice_profile_id: str) -> dict:
    table_name = os.environ.get("VOICE_TABLE")
    if table_name:
        item = boto3.resource("dynamodb").Table(table_name).get_item(Key={"voice_profile_id": voice_profile_id}).get("Item")
        if item:
            # If the profile is seeded without a voice_id, fall back to SSM.
            if not item.get("voice_id"):
                item["voice_id"] = _get_default_voice_id()
            return item
    return {
        "voice_profile_id": voice_profile_id,
        "provider": "elevenlabs",
        "voice_id": _get_default_voice_id() or "REPLACE_WITH_ELEVENLABS_VOICE_ID",
        "model_id": os.environ.get("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5"),
        "stability": "0.85",
        "similarity_boost": "0.90",
        "style": "0.0",
        "use_speaker_boost": True,
    }


def _build_request(text: str, voice_id: str, profile: dict, streaming: bool) -> request.Request:
    endpoint_suffix = "/stream" if streaming else ""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}{endpoint_suffix}"
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("ElevenLabs API key is not configured. Set ELEVENLABS_API_KEY for local dev or ELEVENLABS_API_KEY_PARAM to an SSM SecureString path.")
    body = json.dumps({
        "text": text,
        "model_id": profile.get("model_id") or os.environ.get("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5"),
        "voice_settings": {
            "stability": float(profile.get("stability", 0.85)),
            "similarity_boost": float(profile.get("similarity_boost", 0.90)),
            "style": float(profile.get("style", 0.0)),
            "use_speaker_boost": bool(profile.get("use_speaker_boost", True)),
        },
    }).encode("utf-8")
    return request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
    )


def synthesize_with_elevenlabs(text: str, voice_profile_id: str, meeting_id: str, output_mode: str = "file") -> dict:
    """Synthesize speech via ElevenLabs.

    output_mode=file stores MP3 in S3 and returns an s3_uri.
    output_mode=stream currently returns a presigned S3 URL after using the streaming endpoint,
    which keeps API Gateway simple while exercising the low-latency ElevenLabs path.
    For a real meeting bridge, replace the S3 write loop with direct chunk forwarding to WebRTC.
    """
    profile = _get_voice_profile(voice_profile_id)
    voice_id = profile.get("voice_id")
    if not voice_id or voice_id == "REPLACE_WITH_ELEVENLABS_VOICE_ID":
        raise RuntimeError("ElevenLabs voice_id is not configured. Set ELEVENLABS_VOICE_ID or ELEVENLABS_VOICE_ID_PARAM.")

    streaming = output_mode in {"stream", "streaming"}
    req = _build_request(text=text, voice_id=voice_id, profile=profile, streaming=streaming)
    try:
        with request.urlopen(req, timeout=int(os.environ.get("ELEVENLABS_TIMEOUT_SECONDS", "20"))) as resp:
            audio_bytes = resp.read()
    except error.HTTPError as exc:
        raise RuntimeError(f"ElevenLabs HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore')}") from exc

    bucket = os.environ["AUDIO_BUCKET"]
    key = f"audio/{meeting_id}/{uuid.uuid4()}.mp3"
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=audio_bytes,
        ContentType="audio/mpeg",
        ServerSideEncryption="AES256",
        Metadata={"provider": "elevenlabs", "voice_profile_id": voice_profile_id},
    )
    result = {
        "provider": "elevenlabs",
        "s3_uri": f"s3://{bucket}/{key}",
        "voice_profile_id": voice_profile_id,
        "output_mode": output_mode,
        "bytes": len(audio_bytes),
    }
    if os.environ.get("RETURN_PRESIGNED_AUDIO_URL", "true").lower() == "true":
        result["audio_url"] = boto3.client("s3").generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=int(os.environ.get("AUDIO_URL_TTL_SECONDS", "900")),
        )
    return result
