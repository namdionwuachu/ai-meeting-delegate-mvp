import re

EMAIL_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
AWS_ACCOUNT_ID_REGEX = r"\b\d{12}\b"
AWS_ACCESS_KEY_REGEX = r"\b(AKIA|ASIA)[A-Z0-9]{16}\b"
PHONE_REGEX = r"\b(?:\+44|0)\s?\d{3,4}\s?\d{3}\s?\d{3,4}\b"

def redact_sensitive_text(text: str) -> str:
    text = re.sub(AWS_ACCESS_KEY_REGEX, "[REDACTED_AWS_ACCESS_KEY]", text)
    text = re.sub(EMAIL_REGEX, "[REDACTED_EMAIL]", text)
    text = re.sub(AWS_ACCOUNT_ID_REGEX, "[REDACTED_AWS_ACCOUNT_ID]", text)
    text = re.sub(PHONE_REGEX, "[REDACTED_PHONE]", text)
    return text