import asyncpg, logging

from . import config

log = logging.getLogger(__name__)

# Глобальный пул соединений с PostgreSQL
pool: asyncpg.Pool | None = None


async def connect() -> None:
    """
    Устанавливает пул соединений с базой данных.
    Результат сохраняется в глобальной переменной pool.
    """
    global pool
    pool = await asyncpg.create_pool(
        dsn=config.DATABASE_URL,
        min_size=1,
        max_size=10,
    )
    log.info("PostgreSQL pool ready")


async def close() -> None:
    """
    Закрывает пул соединений (если не был закрыт ранее).
    Вызывается при завершении работы бота.
    """
    global pool
    if pool and not pool._closed:
        await pool.close()
        log.info("PostgreSQL pool closed")
