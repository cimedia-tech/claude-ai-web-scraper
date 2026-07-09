import hashlib
import aiosqlite
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from .config import settings


class URLCache:
    """
    Async SQLite cache to prevent re-scraping and re-extracting already
    processed URLs. Eliminates redundant Claude API calls.
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS url_cache (
                    url_hash    TEXT PRIMARY KEY,
                    url         TEXT NOT NULL,
                    result_json TEXT,
                    scraped_at  TEXT NOT NULL,
                    expires_at  TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cost_log (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    url             TEXT,
                    model           TEXT,
                    input_tokens    INTEGER,
                    output_tokens   INTEGER,
                    estimated_cost  REAL,
                    logged_at       TEXT
                )
            """)
            await db.commit()

    @staticmethod
    def _hash(url: str) -> str:
        return hashlib.sha256(url.encode()).hexdigest()

    async def get(self, url: str) -> str | None:
        """Return cached JSON result if URL is still fresh, else None."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT result_json, expires_at FROM url_cache WHERE url_hash = ?",
                (self._hash(url),)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    result_json, expires_at = row
                    if datetime.fromisoformat(expires_at) > datetime.utcnow():
                        return result_json
        return None

    async def set(self, url: str, result_json: str):
        """Cache a result for TTL hours."""
        now = datetime.utcnow()
        expires = now + timedelta(hours=settings.cache_ttl_hours)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO url_cache
                (url_hash, url, result_json, scraped_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (self._hash(url), url, result_json,
                  now.isoformat(), expires.isoformat()))
            await db.commit()

    async def log_cost(self, url: str, model: str,
                       input_tokens: int, output_tokens: int):
        """Log per-call token usage. Haiku: $1/MTok in, $5/MTok out."""
        cost = (input_tokens / 1_000_000 * 1.0) + (output_tokens / 1_000_000 * 5.0)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO cost_log
                (url, model, input_tokens, output_tokens, estimated_cost, logged_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (url, model, input_tokens, output_tokens, cost,
                  datetime.utcnow().isoformat()))
            await db.commit()
        return cost

    async def total_cost(self) -> float:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT SUM(estimated_cost) FROM cost_log"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] or 0.0

    async def purge_expired(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM url_cache WHERE expires_at < ?",
                (datetime.utcnow().isoformat(),)
            )
            await db.commit()
