from typing import Sequence, Mapping

from . import db


async def save_user(tg_id: int, username: str | None, first: str | None) -> None:
    """
    Добавить пользователя в таблицу users.
    """
    query = """
        INSERT INTO users (telegram_id, username, first_name)
        VALUES ($1, $2, $3)
        ON CONFLICT (telegram_id) DO NOTHING
    """
    async with db.pool.acquire() as conn:
        await conn.execute(query, tg_id, username, first)


"""
async def all_user_ids() -> Sequence[int]:

    rows = await db.pool.fetch("SELECT telegram_id FROM users")
    return [row["telegram_id"] for row in rows]
"""


async def all_user_ids() -> list[int]:
    """
    Список всех Telegram ID зарегистрированных пользователей.
    """
    rows = await db.pool.fetch("SELECT telegram_id FROM users")
    return [r["telegram_id"] for r in rows]


async def get_catalog() -> Sequence[Mapping]:
    """Список телефонов в наличии, отсортированный по цене."""
    query = """
        SELECT id, model, storage, color, price
        FROM phones
        WHERE quantity > 0
        ORDER BY sort_idx DESC, price
    """
    return await db.pool.fetch(query)


async def get_phone(phone_id: str | int):
    """Получить телефон по ID."""
    pid = int(phone_id)
    return await db.pool.fetchrow(
        "SELECT * FROM phones WHERE id = $1",
        pid,
    )


async def add_user_phone(user_id: int, phone_id: str | int) -> None:
    """
    Зафиксировать интерес пользователя к конкретному телефону.
    Повторный интерес обновит поле added_at.
    """
    pid = int(phone_id)
    query = """
        INSERT INTO user_phones (user_id, phone_id)
        VALUES ($1, $2)
        ON CONFLICT (user_id, phone_id)
        DO UPDATE SET added_at = NOW()
    """
    async with db.pool.acquire() as conn:
        await conn.execute(query, user_id, pid)


async def distinct_models() -> list[str]:
    """Уникальные модели, доступные в наличии."""
    rows = await db.pool.fetch(
        """
        SELECT model
        FROM phones
        WHERE quantity > 0
        GROUP BY model
        ORDER BY MAX(sort_idx) DESC, model -- ← главное поле сортировки
        """
    )
    return [r["model"] for r in rows]


async def distinct_storages(model: str):
    """Доступные объёмы памяти для указанной модели."""
    rows = await db.pool.fetch(
        "SELECT DISTINCT storage FROM phones WHERE model=$1 AND quantity>0 ORDER BY storage",
        model,
    )
    return [r["storage"] for r in rows]


async def distinct_colors(model: str, storage: int):
    """Доступные цвета для конкретной модели и объёма памяти."""
    rows = await db.pool.fetch(
        """
        SELECT DISTINCT color
        FROM phones
        WHERE model=$1 AND storage=$2 AND quantity>0
        ORDER BY color
        """,
        model, storage,
    )
    return [r["color"] for r in rows]


async def get_phone_by_attrs(model: str, storage: int, color: str):
    """Получить телефон по тройке: модель, объём, цвет."""
    return await db.pool.fetchrow(
        """
        SELECT * FROM phones
        WHERE model=$1 AND storage=$2 AND color=$3
        LIMIT 1
        """,
        model, storage, color,
    )


async def user_ids_for_models(models: list[str]) -> list[int]:
    """Получить пользователей, интересовавшихся любой из указанных моделей."""
    rows = await db.pool.fetch(
        """
        SELECT DISTINCT up.user_id          -- это telegram_id
        FROM user_phones up
        JOIN phones      p ON p.id = up.phone_id
        WHERE p.model = ANY($1::text[])
        """,
        models,
    )
    return [r["user_id"] for r in rows]