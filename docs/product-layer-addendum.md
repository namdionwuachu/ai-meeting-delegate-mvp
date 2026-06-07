# Product Layer Addendum: Guardrails, Test UI, Meeting, Avatar

This release adds the product-facing layers on top of the Persona + RAG + Voice MVP.

## Added

### 6. Policy / Guardrails
- Restricted topic rules in `services/policy/restricted_topics.py`
- Bedrock Guardrails independent `ApplyGuardrail` adapter in `services/policy/bedrock_guardrails.py`
- Output guardrail check in `services/policy/output_guardrails.py`
- SNS escalation helper in `services/policy/escalation.py`
- Orchestrator now escalates blocked/cautious responses

### 7. Test UI
- Static browser UI in `frontend/test-ui/`
- Flow: ask question → delegate responds → optional cloned voice playback
- Set the API Gateway base URL in the page and click **Ask Delegate** or **Ask + Voice**

### 8. Meeting Integration
- Recall.ai connector skeleton in `services/meeting/recall_client.py`
- Turn-taking/VAD decision helper in `services/meeting/turn_taking.py`
- Disclosure message helper and `/meeting/join` Lambda handler
- Native Zoom/Teams connectors remain future adapters behind the same boundary

### 9. Avatar Layer
- HeyGen adapter skeleton in `services/avatar/heygen_client.py`
- D-ID fallback adapter skeleton in `services/avatar/did_client.py`
- Router with failover to voice-only mode in `services/avatar/avatar_router.py`
- `/avatar/speak` Lambda handler

## CDK updates

The CDK stack now includes:
- Meeting connector Lambda
- Avatar Lambda
- SSM Parameter Store placeholders for Recall, HeyGen, and D-ID
- API routes: `/meeting/join` and `/avatar/speak`
- IAM permission for `bedrock:ApplyGuardrail`

## Current limits

This is still an MVP-ready codebase, not a certified production bot. Provider-specific endpoints for Recall.ai, HeyGen, and D-ID are isolated in adapters so you can update them quickly if your account/region/API version differs.

## Deployment notes

After deployment, update the parameter values:

```bash
aws ssm put-parameter --type SecureString --overwrite --name /AIDelegateStack/recall/api-key --value '<recall-api-key>'
aws ssm put-parameter --type SecureString --overwrite --name /AIDelegateStack/heygen/api-key --value '<heygen-api-key>'
aws ssm put-parameter --type SecureString --overwrite --name /AIDelegateStack/did/api-key --value '<did-api-key>'
```

If using Bedrock Guardrails, set Lambda env vars:

```text
BEDROCK_GUARDRAIL_ID=<your-guardrail-id>
BEDROCK_GUARDRAIL_VERSION=<version>
```

## Test UI

Open:

```text
frontend/test-ui/index.html
```

Paste the deployed API Gateway base URL and test:

```text
Ask question → get persona answer → play cloned voice
```
