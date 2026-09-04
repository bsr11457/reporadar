import re

PATTERNS = [
    (re.compile(r'(?i)\b(sk-[A-Za-z0-9_-]{20,})\b'), "[REDACTED_OPENAI_KEY]"),
    (re.compile(r'(?i)\b(gsk_[A-Za-z0-9_-]{20,})\b'), "[REDACTED_GROQ_KEY]"),
    (re.compile(r'(?i)\b(AUTHORIZATION\s*[:=]\s*Bearer\s+)[A-Za-z0-9._-]+'), r'\1[REDACTED]'),
    (re.compile(r'(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*[\'"][^\'"]+[\'"]'), r'\1="[REDACTED]"'),
    (re.compile(r'(?i)\b(api[_-]?key|token|secret|password)\s*=\s*[^\s#]+'), r'\1="[REDACTED]"'),
]

def redact_secrets(text: str) -> str:
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text
