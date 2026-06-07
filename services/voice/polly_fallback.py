import os
import uuid

import boto3


def synthesize_with_polly(text: str, meeting_id: str) -> dict:
    polly = boto3.client("polly")
    response = polly.synthesize_speech(
        Text=text,
        OutputFormat="mp3",
        VoiceId=os.environ.get("POLLY_VOICE_ID", "Amy"),
        Engine="neural",
    )
    audio = response["AudioStream"].read()
    bucket = os.environ["AUDIO_BUCKET"]
    key = f"audio/{meeting_id}/{uuid.uuid4()}-polly.mp3"
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=audio,
        ContentType="audio/mpeg",
        ServerSideEncryption="AES256",
    )
    return {"provider": "polly", "s3_uri": f"s3://{bucket}/{key}"}
