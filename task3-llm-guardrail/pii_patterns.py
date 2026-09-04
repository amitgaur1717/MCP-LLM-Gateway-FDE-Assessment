import re


# -------------------------------------------------------------------
# PII detection patterns
# -------------------------------------------------------------------
# These patterns identify sensitive information that must never be
# returned to the client in its original form.
#
# The gateway is responsible for applying these patterns while the
# response is still being streamed.
# -------------------------------------------------------------------

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


SSN_PATTERN = re.compile(
    r"\b\d{3}-\d{2}-\d{4}\b"
)


CREDIT_CARD_PATTERN = re.compile(
    r"\b(?:\d[ -]?){13,19}\b"
)


def redact_complete_text(text: str) -> str:
    """
    Redact PII from a text segment.

    This function operates only on the segment supplied to it.
    It does not maintain the complete LLM response in memory.
    """

    text = EMAIL_PATTERN.sub(
        "[REDACTED]",
        text,
    )

    text = SSN_PATTERN.sub(
        "[REDACTED]",
        text,
    )

    text = CREDIT_CARD_PATTERN.sub(
        "[REDACTED]",
        text,
    )

    return text