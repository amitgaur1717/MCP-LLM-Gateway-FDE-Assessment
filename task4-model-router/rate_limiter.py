import asyncio
import time

from usage_store import UsageStore


# -------------------------------------------------------------------
# Rate-limit configuration
# -------------------------------------------------------------------

WINDOW_SECONDS = 60
TOKEN_LIMIT = 50_000


class RateLimiter:
    """
    Token-aware sliding-window rate limiter.

    Each tenant has an independent token budget.

    Maximum:
        50,000 tokens
        within a 60-second rolling window.
    """

    def __init__(self):
        # -----------------------------------------------------------
        # The lock protects the check-and-record operation.
        #
        # Without this lock, two concurrent requests could both
        # observe the same usage and exceed the tenant's limit.
        # -----------------------------------------------------------

        self.lock = asyncio.Lock()

        # -----------------------------------------------------------
        # Persistence is delegated to UsageStore.
        # -----------------------------------------------------------

        self.store = UsageStore()

    async def allow(
        self,
        tenant_key: str,
        tokens: int,
    ) -> bool:
        """
        Determine whether a tenant is allowed to consume tokens.

        Returns:
            True  -> request is within the limit
            False -> request would exceed the limit
        """

        # -----------------------------------------------------------
        # The entire check + record operation must be atomic from
        # the application's point of view.
        # -----------------------------------------------------------

        async with self.lock:

            now = time.time()

            window_start = (
                now - WINDOW_SECONDS
            )

            # -------------------------------------------------------
            # Remove expired records.
            # -------------------------------------------------------

            self.store.remove_expired(
                window_start
            )

            # -------------------------------------------------------
            # Calculate current tenant usage.
            # -------------------------------------------------------

            current_usage = self.store.get_usage(
                tenant_key,
                window_start,
            )

            # -------------------------------------------------------
            # Check whether the new request would exceed the limit.
            # -------------------------------------------------------

            if current_usage + tokens > TOKEN_LIMIT:
                return False

            # -------------------------------------------------------
            # Record the token allocation only after the request
            # has passed the limit check.
            # -------------------------------------------------------

            self.store.record_usage(
                tenant_key=tenant_key,
                tokens=tokens,
                timestamp=now,
            )

            return True