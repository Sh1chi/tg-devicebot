from typing import Sequence, Mapping
from . import db


# ---------- USERS ----------

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


async def all_user_ids() -> Sequence[int]:
    rows = await db.pool.fetch("SELECT telegram_id FROM users")
    return [row["telegram_id"] for row in rows]


# ---------- PHONES ----------

async def get_catalog() -> Sequence[Mapping]:
    query = """
        SELECT id, model, storage, color, price
        FROM phones
        WHERE quantity > 0
        ORDER BY price
    """
    return await db.pool.fetch(query)


async def get_phone(phone_id: str | int):
    """
    Вернёт одну строку из phones по её числовому id.
    """
    pid = int(phone_id)                    # приводим к int
    return await db.pool.fetchrow(
        "SELECT * FROM phones WHERE id = $1",
        pid,
    )


async def add_user_phone(user_id: int, phone_id: str | int) -> None:
    """
    Записать факт интереса пользователя к телефону.
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

