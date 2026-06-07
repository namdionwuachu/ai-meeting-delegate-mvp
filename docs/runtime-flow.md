# Runtime Flow

```text
POST /delegate/respond
  ├─ policy.check_policy()
  ├─ persona.load_persona()
  ├─ rag.retrieve_context()
  ├─ examples.load_examples()
  ├─ response_generator.generate_delegate_response()
  ├─ confidence.score_confidence()
  ├─ voice.synthesize_voice() optional
  └─ audit.write_audit_record()
```

## Phase boundary

This MVP returns text and optionally audio. The next phase is to plug the audio output into a meeting bot.
