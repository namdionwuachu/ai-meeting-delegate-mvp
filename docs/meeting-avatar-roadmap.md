# Meeting + Avatar Roadmap

## Meeting phase

1. Use Recall.ai connector first for speed.
2. Bot joins as `Namdi [AI Delegate]`.
3. Bot announces proactive disclosure.
4. Transcripts are sent to `/delegate/respond`.
5. Generated voice output is injected back into the meeting audio channel.
6. Add native Zoom/Teams connectors later if required.

## Avatar phase

1. Start voice-only.
2. Add HeyGen streaming when voice path is stable.
3. Add D-ID as fallback.
4. If both avatar providers fail, continue voice-only.
5. Always keep a disclosure message visible or spoken at meeting start.

## Failover chain

```text
HeyGen + ElevenLabs
↓
D-ID + ElevenLabs
↓
ElevenLabs voice only
↓
Polly voice only
↓
Text-only transcript response
```
