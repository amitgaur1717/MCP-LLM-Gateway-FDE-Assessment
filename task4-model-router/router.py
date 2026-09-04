
import httpx

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

from rate_limiter import RateLimiter


# -----------------------------------------------------------
# FastAPI application
# -----------------------------------------------------------

app = FastAPI(title="Model Fallback Router")


# -----------------------------------------------------------
# Upstream model endpoints
# -----------------------------------------------------------

# Primary model provider.
PRIMARY_URL = "http://localhost:9100/generate"

# Secondary model provider used when the primary fails
# because of timeout or HTTP 429.
SECONDARY_URL = "http://localhost:9200/generate"


# -----------------------------------------------------------
# Rate limiter
# -----------------------------------------------------------

# Shared rate limiter instance.
#
# The RateLimiter is responsible for enforcing the
# per-tenant token limit within the configured time window.
rate_limiter = RateLimiter()


# -----------------------------------------------------------
# Helper: Call an upstream model
# -----------------------------------------------------------

async def call_model(url: str, payload: dict):
    """
    Send the request to an upstream model provider.

    A maximum timeout of 3 seconds is applied to every
    upstream request.
    """

    async with httpx.AsyncClient(timeout=3.0) as client:
        return await client.post(
            url,
            json=payload,
        )


# -----------------------------------------------------------
# Main generation endpoint
# -----------------------------------------------------------

@app.post("/generate")
async def generate(
    payload: dict,
    x_tenant_key: str | None = Header(default=None),
):
    """
    Generate a response using the primary model.

    The request flow is:

        1. Validate tenant API key
        2. Validate token count
        3. Check token rate limit
        4. Call primary model
        5. Fall back to secondary model on timeout/429
        6. Return sanitized errors
    """

    # -------------------------------------------------------
    # 1. Validate tenant key
    # -------------------------------------------------------

    # A tenant key is required for rate limiting.
    #
    # Missing key:
    #     X-Tenant-Key header does not exist
    #
    # Empty key:
    #     X-Tenant-Key: ""
    #
    # Whitespace-only key:
    #     X-Tenant-Key: "   "
    #
    # All of these are treated as unauthorized.
    if not x_tenant_key or not x_tenant_key.strip():
        return JSONResponse(
            status_code=401,
            content={
                "error": "Unauthorized",
            },
        )

    # -------------------------------------------------------
    # 2. Validate token count
    # -------------------------------------------------------

    # Read the token count supplied by the request.
    tokens = payload.get("tokens", 0)

    # Token count must be an integer and cannot be negative.
    if not isinstance(tokens, int) or tokens < 0:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid token count",
            },
        )

    # -------------------------------------------------------
    # 3. Check tenant token rate limit
    # -------------------------------------------------------

    # Ask the rate limiter whether this request can consume
    # the requested number of tokens.
    allowed = await rate_limiter.allow(
        x_tenant_key,
        tokens,
    )

    # If the tenant has exceeded the configured token limit,
    # reject the request with HTTP 429.
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Token rate limit exceeded",
            },
        )

    # -------------------------------------------------------
    # 4. Call primary model
    # -------------------------------------------------------

    try:
        response = await call_model(
            PRIMARY_URL,
            payload,
        )

        # ---------------------------------------------------
        # 5. Fallback on primary HTTP 429
        # ---------------------------------------------------

        # If the primary provider is rate-limiting the request,
        # send the request to the secondary provider.
        if response.status_code == 429:
            return await fallback(payload)

        # ---------------------------------------------------
        # Return primary response
        # ---------------------------------------------------

        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )

    # -------------------------------------------------------
    # Primary provider timeout
    # -------------------------------------------------------

    except httpx.TimeoutException:

        # If the primary provider takes longer than 3 seconds,
        # try the secondary provider.
        return await fallback(payload)

    # -------------------------------------------------------
    # Primary provider connection/request failure
    # -------------------------------------------------------

    except httpx.RequestError:

        # Do not expose internal exception details or stack
        # traces to the client.
        return JSONResponse(
            status_code=502,
            content={
                "error": "Primary model unavailable",
            },
        )


# -----------------------------------------------------------
# Fallback model
# -----------------------------------------------------------

async def fallback(payload: dict):
    """
    Call the secondary model provider.

    This function is called when the primary model:
        - returns HTTP 429, or
        - times out after 3 seconds.
    """

    try:

        # ---------------------------------------------------
        # Call secondary provider
        # ---------------------------------------------------

        response = await call_model(
            SECONDARY_URL,
            payload,
        )

        # ---------------------------------------------------
        # Return secondary response
        # ---------------------------------------------------

        return JSONResponse(
            status_code=response.status_code,
            content=response.json(),
        )

    # -------------------------------------------------------
    # Secondary provider timeout
    # -------------------------------------------------------

    except httpx.TimeoutException:

        # Both model providers timed out.
        return JSONResponse(
            status_code=504,
            content={
                "error": "Model providers timed out",
            },
        )

    # -------------------------------------------------------
    # Secondary provider request failure
    # -------------------------------------------------------

    except httpx.RequestError:

        # Hide internal provider/network details.
        return JSONResponse(
            status_code=502,
            content={
                "error": "Model provider unavailable",
            },
        )
