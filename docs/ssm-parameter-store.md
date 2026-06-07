# SSM Parameter Store configuration

This build uses AWS Systems Manager Parameter Store instead of AWS Secrets Manager to avoid the monthly per-secret charge for the MVP.

Use `SecureString` for provider API keys and voice/avatar IDs.

## Parameter paths

The CDK stack passes these paths into Lambda environment variables:

```text
/<STACK_NAME>/elevenlabs/api-key
/<STACK_NAME>/elevenlabs/voice-id
/<STACK_NAME>/recall/api-key
/<STACK_NAME>/heygen/api-key
/<STACK_NAME>/heygen/avatar-id
/<STACK_NAME>/did/api-key
/<STACK_NAME>/bedrock/guardrail-id
/<STACK_NAME>/bedrock/guardrail-version
```

## Quick setup

```bash
export AWS_REGION=eu-west-2
export ELEVENLABS_API_KEY='your-key'
export ELEVENLABS_VOICE_ID='your-voice-id'

# Optional later
export RECALL_API_KEY='your-recall-key'
export HEYGEN_API_KEY='your-heygen-key'
export HEYGEN_AVATAR_ID='your-avatar-id'
export DID_API_KEY='your-did-key'
export BEDROCK_GUARDRAIL_ID='your-guardrail-id'
export BEDROCK_GUARDRAIL_VERSION='DRAFT-or-version'

./scripts/setup_ssm_parameters.sh AIDelegateStack
```

## Local development override

For local tests, you can still set direct environment variables:

```text
ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID
RECALL_API_KEY
HEYGEN_API_KEY
HEYGEN_AVATAR_ID
DID_API_KEY
BEDROCK_GUARDRAIL_ID
BEDROCK_GUARDRAIL_VERSION
```

The runtime checks direct environment variables first, then falls back to SSM Parameter Store.

## IAM

The CDK stack grants Lambdas:

```text
ssm:GetParameter
ssm:GetParameters
ssm:GetParametersByPath
kms:Decrypt via SSM
```

restricted to the stack parameter prefix where possible.
