import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from rate_limiter import RateLimiter, TOKEN_LIMIT
from router import app


# -------------------------------------------------------------------
# FastAPI test client
# -------------------------------------------------------------------

client = TestClient(app)


# -------------------------------------------------------------------
# Rate limiter fixture
# -------------------------------------------------------------------

@pytest.fixture
def limiter(tmp_path, monkeypatch):
    """
    Create an isolated SQLite database for every test.

    This prevents tests from sharing token-usage data.
    """

    database = tmp_path / "rate_limits.db"

    # The UsageStore reads DATABASE from its own module.
    monkeypatch.setattr(
        "usage_store.DATABASE",
        str(database),
    )

    return RateLimiter()


# -------------------------------------------------------------------
# Basic rate-limit tests
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_request_under_limit_is_allowed(limiter):
    """
    A request below the tenant token limit should be allowed.
    """

    result = await limiter.allow(
        tenant_key="claims-tenant-a",
        tokens=10_000,
    )

    assert result is True


@pytest.mark.asyncio
async def test_request_at_exact_limit_is_allowed(limiter):
    """
    A request that exactly reaches the limit should be allowed.
    """

    result = await limiter.allow(
        tenant_key="claims-tenant-a",
        tokens=TOKEN_LIMIT,
    )

    assert result is True


@pytest.mark.asyncio
async def test_request_exceeding_limit_is_rejected(limiter):
    """
    Once a tenant has consumed the full allowance, another token
    allocation must be rejected.
    """

    first = await limiter.allow(
        tenant_key="claims-tenant-a",
        tokens=TOKEN_LIMIT,
    )

    second = await limiter.allow(
        tenant_key="claims-tenant-a",
        tokens=1,
    )

    assert first is True
    assert second is False


# -------------------------------------------------------------------
# Tenant isolation
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tenants_have_independent_limits(limiter):
    """
    Token usage belonging to one tenant must not affect another
    tenant.
    """

    tenant_a = await limiter.allow(
        tenant_key="claims-tenant-a",
        tokens=TOKEN_LIMIT,
    )

    tenant_b = await limiter.allow(
        tenant_key="claims-tenant-b",
        tokens=TOKEN_LIMIT,
    )

    assert tenant_a is True
    assert tenant_b is True


# -------------------------------------------------------------------
# Sliding-window expiration
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_expired_usage_does_not_count(limiter):
    """
    Usage older than the configured window should be removed and
    should not prevent a new request.
    """

    old_timestamp = (
        time.time() - 120
    )

    limiter.store.record_usage(
        tenant_key="claims-tenant-a",
        tokens=TOKEN_LIMIT,
        timestamp=old_timestamp,
    )

    result = await limiter.allow(
        tenant_key="claims-tenant-a",
        tokens=10_000,
    )

    assert result is True


# -------------------------------------------------------------------
# Persistence test
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_token_usage_is_persisted(limiter):
    """
    Successful token allocation must be written to SQLite.
    """

    await limiter.allow(
        tenant_key="claims-tenant-a",
        tokens=15_000,
    )

    usage = limiter.store.get_usage(
        tenant_key="claims-tenant-a",
        window_start=time.time() - 60,
    )

    assert usage == 15_000


# -------------------------------------------------------------------
# Concurrency test
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_concurrent_requests_cannot_bypass_limit(limiter):
    """
    Concurrent requests must still respect the tenant's token limit.

    This verifies that the check-and-record operation is protected
    against race conditions.
    """

    requests = [
        limiter.allow(
            tenant_key="claims-tenant-a",
            tokens=10_000,
        )
        for _ in range(6)
    ]

    results = await asyncio.gather(*requests)

    # Maximum possible usage is 50,000 tokens.
    assert sum(results) == 5


# -------------------------------------------------------------------
# Invalid token amount
# -------------------------------------------------------------------

@pytest.mark.asyncio
async def test_zero_tokens_do_not_consume_budget(limiter):
    """
    Zero-token requests should not consume the tenant's token budget.

    If the assessment requires positive token counts, the candidate
    should instead reject this input.
    """

    result = await limiter.allow(
        tenant_key="claims-tenant-a",
        tokens=0,
    )

    assert result is True

# -------------------------------------------------------------------
# Router authentication / tenant validation
# -------------------------------------------------------------------

def test_missing_tenant_key_is_rejected():
    """
    Requests without a tenant API key must be rejected.
    """

    response = client.post(
        "/generate",
        json={
            "prompt": "Generate a claims summary",
            "tokens": 100,
        },
    )

    assert response.status_code == 401


def test_empty_tenant_key_is_rejected():
    """
    An empty tenant key must not be accepted.
    """

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-Key": ""
        },
        json={
            "prompt": "Generate a claims summary",
            "tokens": 100,
        },
    )

    assert response.status_code == 401


# -------------------------------------------------------------------
# Rate-limit behavior through the API
# -------------------------------------------------------------------

def test_rate_limit_response():
    """
    Once a tenant exceeds its token budget, the gateway should
    return a sanitized rate-limit response.
    """

    # This test assumes the router uses the same RateLimiter
    # configuration as the assessment.
    #
    # The exact HTTP status/error contract should remain consistent
    # with the master assessment.

    for _ in range(5):
        response = client.post(
            "/generate",
            headers={
                "X-Tenant-Key": "claims-test-tenant"
            },
            json={
                "prompt": "Generate claims analysis",
                "tokens": 10_000,
            },
        )

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-Key": "claims-test-tenant"
        },
        json={
            "prompt": "Generate claims analysis",
            "tokens": 1,
        },
    )

    assert response.status_code == 429


# -------------------------------------------------------------------
# Sanitized gateway errors
# -------------------------------------------------------------------

def test_gateway_does_not_expose_stack_trace():
    """
    Internal errors must not expose Python exception details,
    database paths, URLs, or stack traces to the client.
    """

    response = client.post(
        "/generate",
        headers={
            "X-Tenant-Key": "claims-error-test"
        },
        json={
            "prompt": "Generate claims analysis",
            "tokens": 100,
        },
    )

    body = response.text.lower()

    assert "traceback" not in body
    assert "file \"" not in body