#!/usr/bin/env bash
set -euo pipefail

STACK_NAME=${1:-AIDelegateStack}
REGION=${AWS_REGION:-eu-west-2}

# Usage:
#   ELEVENLABS_API_KEY=... ELEVENLABS_VOICE_ID=... ./scripts/setup_ssm_parameters.sh AIDelegateStack
# Optional:
#   RECALL_API_KEY=... HEYGEN_API_KEY=... HEYGEN_AVATAR_ID=... DID_API_KEY=...
#   BEDROCK_GUARDRAIL_ID=... BEDROCK_GUARDRAIL_VERSION=...

put_secure() {
  local name=$1
  local value=${2:-}
  if [[ -n "$value" ]]; then
    aws ssm put-parameter \
      --region "$REGION" \
      --name "/${STACK_NAME}/${name}" \
      --type SecureString \
      --value "$value" \
      --overwrite >/dev/null
    echo "Stored SecureString: /${STACK_NAME}/${name}"
  else
    echo "Skipped /${STACK_NAME}/${name} (value not set)"
  fi
}

put_string() {
  local name=$1
  local value=${2:-}
  if [[ -n "$value" ]]; then
    aws ssm put-parameter \
      --region "$REGION" \
      --name "/${STACK_NAME}/${name}" \
      --type String \
      --value "$value" \
      --overwrite >/dev/null
    echo "Stored String: /${STACK_NAME}/${name}"
  else
    echo "Skipped /${STACK_NAME}/${name} (value not set)"
  fi
}

put_secure "elevenlabs/api-key" "${ELEVENLABS_API_KEY:-}"
put_secure "elevenlabs/voice-id" "${ELEVENLABS_VOICE_ID:-}"
put_secure "recall/api-key" "${RECALL_API_KEY:-}"
put_secure "heygen/api-key" "${HEYGEN_API_KEY:-}"
put_secure "heygen/avatar-id" "${HEYGEN_AVATAR_ID:-}"
put_secure "did/api-key" "${DID_API_KEY:-}"

put_string "bedrock/guardrail-id" "${BEDROCK_GUARDRAIL_ID:-}"
put_string "bedrock/guardrail-version" "${BEDROCK_GUARDRAIL_VERSION:-}"
