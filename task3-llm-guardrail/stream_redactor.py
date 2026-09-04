from pii_patterns import redact_complete_text


class StreamRedactor:
    """
    Stateful redactor for streaming LLM responses.

    Keeps a bounded trailing buffer so PII values split across
    streaming chunks can be detected.
    """

    def __init__(self, buffer_size: int = 50):
        if buffer_size <= 0:
            raise ValueError("buffer_size must be greater than 0")

        self.buffer_size = buffer_size
        self.buffer = ""

        # Minimum context needed to safely detect the supported
        # PII patterns across chunk boundaries.
        self.min_buffer_size = 32

    def process_chunk(self, chunk: str) -> str:
        """
        Process one streaming chunk.

        Retains a bounded suffix so sensitive values split across
        chunks are not emitted before they can be detected.
        """

        if not chunk:
            return ""

        self.buffer += chunk

        effective_buffer_size = max(
            self.buffer_size,
            self.min_buffer_size
        )

        # Keep buffering until we have enough context.
        if len(self.buffer) <= effective_buffer_size:
            return ""

        # Everything before the protected suffix is safe to emit.
        safe_part = self.buffer[:-effective_buffer_size]

        # Retain only bounded state.
        self.buffer = self.buffer[-effective_buffer_size:]

        return redact_complete_text(safe_part)

    def finalize(self) -> str:
        """
        Redact and return all remaining buffered content.
        """

        if not self.buffer:
            return ""

        remaining = self.buffer
        self.buffer = ""

        return redact_complete_text(remaining)