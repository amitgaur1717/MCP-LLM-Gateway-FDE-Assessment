from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import httpx

from stream_redactor import redact_text


app = FastAPI(title="LLM Streaming Guardrail")

UPSTREAM_URL = "http://localhost:9000/generate"


@app.post("/generate")
async def generate(payload: dict):
    # Stream the provider response instead of waiting for the full response.
    async def stream_response():
        buffer = ""

        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    UPSTREAM_URL,
                    json=payload,
                ) as response:

                    async for chunk in response.aiter_text():
                        # Keep only a small buffer for patterns split across chunks.
                        buffer += chunk

                        # Keep the final part because sensitive data can span chunks.
                        if len(buffer) > 100:
                            safe_part = buffer[:-50]
                            buffer = buffer[-50:]

                            yield redact_text(safe_part)

                    # Process whatever remains after streaming finishes.
                    if buffer:
                        yield redact_text(buffer)

        except httpx.RequestError:
            # Never expose upstream exception details.
            yield "[Gateway Error] Upstream provider unavailable."

    return StreamingResponse(
        stream_response(),
        media_type="text/plain",
    )