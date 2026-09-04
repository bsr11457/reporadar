from redaction import redact_secrets

def test_redacts_groq_key():
    text = 'GROQ_API_KEY="gsk_abcdefghijklmnopqrstuvwxyz123456789"'
    assert "gsk_" not in redact_secrets(text)
