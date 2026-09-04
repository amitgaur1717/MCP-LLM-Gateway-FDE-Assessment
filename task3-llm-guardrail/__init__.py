from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import httpx

from stream_redactor import StreamRedactor


app = FastAPI(
    title="Enterprise Claims LLM Guardrail"
)


# -------------------------------------------------------------------
# Mock upstream LLM provider
# -------------------------------------------------------------------
# The candidate does not need to implement the provider.
# The gateway must consume its response as a stream.
# -------------------------------------------------------------------

UPSTREAM_URL = "http://localhost:9000/generate"


@app.post("/generate")
async def generate(payload: dict):
    """
    Proxy an LLM request while applying PII redaction to the
    streaming response.

    Requirements:
    - Do not wait for the complete provider response.
    - Process chunks as they arrive.
    - Prevent PII from reaching the client.
    - Handle PII split across chunks.
    - Do not accumulate the complete response.
    - Do not expose upstream exception details.
    """

    async def stream_response():
        # -----------------------------------------------------------
        # Stateful redactor.
        # -----------------------------------------------------------
        redactor = StreamRedactor(
            buffer_size=50
        )

        try:
            # -------------------------------------------------------
            # Maintain an async connection to the upstream provider.
            # -------------------------------------------------------
            async with httpx.AsyncClient(
                timeout=None
            ) as client:

                async with client.stream(
                    "POST",
                    UPSTREAM_URL,
                    json=payload,
                ) as response:

                    # ------------------------------------------------
                    # Process each provider chunk independently.
                    # ------------------------------------------------
                    async for chunk in response.aiter_text():

                        safe_output = redactor.process_chunk(
                            chunk
                        )

                        if safe_output:
                            yield safe_output

                    # ------------------------------------------------
                    # Flush the remaining bounded buffer.
                    # ------------------------------------------------
                    final_output = redactor.finalize()

                    if final_output:
                        yield final_output

        except httpx.RequestError:
            # -------------------------------------------------------
            # Never expose internal upstream exception information.
            # -------------------------------------------------------
            yield (
                "[Gateway Error] "
                "Upstream provider unavailable."
            )

    # ---------------------------------------------------------------
    # Return the response as a streaming text response.
    # ---------------------------------------------------------------

    return StreamingResponse(
        stream_response(),
        media_type="text/plain",
    )