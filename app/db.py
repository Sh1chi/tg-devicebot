# app/db.py
import asyncpg, logging
from . import config   # в .env добавьте DATABASE_URL

log = logging.getLogger(__name__)

pool: asyncpg.Pool | None = None      # будет создан в main.py


async def connect() -> None:
    """Поднять пул к PostgreSQL, хранится в глобальной переменной pool."""
    global pool
    pool = await asyncpg.create_pool(
        dsn=config.DATABASE_URL,
        min_size=1,
        max_size=10,
    )
    log.info("PostgreSQL pool ready")


async def close() -> None:
    """Закрыть пул при остановке бота."""
    global pool
    if pool and not pool._closed:
        await pool.close()
        log.info("PostgreSQL pool closed")
