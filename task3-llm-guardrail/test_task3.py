from stream_redactor import StreamRedactor
from pii_patterns import redact_complete_text


def test_email_redaction():
    """
    Normal email addresses must be redacted.
    """

    text = "Contact john@example.com for assistance."

    result = redact_complete_text(text)

    assert "john@example.com" not in result
    assert "[REDACTED]" in result


def test_ssn_redaction():
    """
    SSNs must never appear in the sanitized output.
    """

    text = "Claimant SSN: 123-45-6789"

    result = redact_complete_text(text)

    assert "123-45-6789" not in result
    assert "[REDACTED]" in result


def test_credit_card_redaction():
    """
    Credit-card numbers must be removed from the output.
    """

    text = "Payment card: 4111 1111 1111 1111"

    result = redact_complete_text(text)

    assert "4111 1111 1111 1111" not in result
    assert "[REDACTED]" in result


def test_email_split_across_chunks():
    """
    A PII value may be split across two provider chunks.

    The redactor must retain enough state to detect the complete
    email address.
    """

    redactor = StreamRedactor(
        buffer_size=10
    )

    output = ""

    output += redactor.process_chunk(
        "Contact john@exa"
    )

    output += redactor.process_chunk(
        "mple.com for help."
    )

    output += redactor.finalize()

    assert "john@example.com" not in output
    assert "[REDACTED]" in output


def test_ssn_split_across_chunks():
    """
    SSNs split across streaming chunks must also be redacted.
    """

    redactor = StreamRedactor(
        buffer_size=10
    )

    output = ""

    output += redactor.process_chunk(
        "SSN: 123-45"
    )

    output += redactor.process_chunk(
        "-6789"
    )

    output += redactor.finalize()

    assert "123-45-6789" not in output
    assert "[REDACTED]" in output


def test_redactor_does_not_keep_complete_response():
    """
    The redactor should retain only a bounded trailing buffer,
    rather than the entire generated response.
    """

    redactor = StreamRedactor(
        buffer_size=50
    )

    large_chunk = "A" * 10_000

    redactor.process_chunk(
        large_chunk
    )

    assert len(redactor.buffer) <= 50