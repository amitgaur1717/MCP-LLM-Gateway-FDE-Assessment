import sqlite3
import time


DATABASE = "rate_limits.db"


class UsageStore:
    """
    Persistence layer for tenant token usage.

    This class is responsible only for SQLite operations.
    Rate-limit decision logic remains in RateLimiter.
    """

    def __init__(self):
        self._initialize_database()

    def _initialize_database(self):
        """
        Create the token usage table if it does not already exist.
        """

        with sqlite3.connect(DATABASE) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS token_usage (
                    tenant_key TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    tokens INTEGER NOT NULL
                )
                """
            )

            connection.commit()

    def remove_expired(self, window_start: float):
        """
        Delete usage records outside the active rate-limit window.
        """

        with sqlite3.connect(DATABASE) as connection:
            connection.execute(
                """
                DELETE FROM token_usage
                WHERE timestamp < ?
                """,
                (window_start,),
            )

            connection.commit()

    def get_usage(
        self,
        tenant_key: str,
        window_start: float,
    ) -> int:
        """
        Return the number of tokens consumed by a tenant
        during the active window.
        """

        with sqlite3.connect(DATABASE) as connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(tokens), 0)
                FROM token_usage
                WHERE tenant_key = ?
                  AND timestamp >= ?
                """,
                (
                    tenant_key,
                    window_start,
                ),
            ).fetchone()

        return int(row[0])

    def record_usage(
        self,
        tenant_key: str,
        tokens: int,
        timestamp: float | None = None,
    ):
        """
        Record a successful token allocation for a tenant.
        """

        if timestamp is None:
            timestamp = time.time()

        with sqlite3.connect(DATABASE) as connection:
            connection.execute(
                """
                INSERT INTO token_usage
                (tenant_key, timestamp, tokens)
                VALUES (?, ?, ?)
                """,
                (
                    tenant_key,
                    timestamp,
                    tokens,
                ),
            )

            connection.commit()