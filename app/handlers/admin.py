import asyncio, shlex
from aiogram import Router, types
from aiogram.filters import Command
from .. import models, config, logger

router = Router()
log = logger.logging.getLogger(__name__)

def admin_only(handler):
    async def wrapper(m: types.Message, *args, **kwargs):
        if m.from_user.id not in config.ADMIN_IDS:
            log.warning("User %s tried admin cmd %s", m.from_user.id, m.text.split()[0])
            return await m.reply("⛔️ Доступ только для админа")
        return await handler(m, *args, **kwargs)
    return wrapper

# /broadcast <текст>
@router.message(Command("broadcast"))
@admin_only
async def broadcast(m: types.Message):
    if " " not in m.text:
        return await m.reply("Использование: /broadcast сообщение")

    _, text = m.text.split(" ", 1)
    ok = fail = 0
    for uid in models.users:
        try:
            await m.bot.send_message(uid, f"🛎️ {text}")
            ok += 1
            await asyncio.sleep(0.04)        # ~25 msg/sec
        except Exception as e:
            fail += 1
            log.exception("Broadcast to %s failed: %s", uid, e)

    log.info("Broadcast by %s: '%s' (ok=%d, fail=%d)",
             m.from_user.id, text, ok, fail)
    await m.reply(f"Рассылка завершена ✅: {ok} успешных, {fail} ошибок")

# /addphone id "Название" цена
@router.message(Command("addphone"))
@admin_only
async def add_phone(m: types.Message):
    try:
        parts = shlex.split(m.text, posix=False)
        if len(parts) < 4:
            raise ValueError
        _, prod_id, name, price = parts[:4]
    except ValueError:
        return await m.reply(
            "Использование:\n"
            "/addphone <id> \"Название\" <Цена>\n"
            "Пример:\n"
            "/addphone 15promax512 \"iPhone 15 Pro Max 512 GB\" 149990"
        )

    if any(p["id"] == prod_id for p in models.catalog):
        log.warning("Admin %s tried to add existing id %s", m.from_user.id, prod_id)
        return await m.reply("ID уже существует.")

    models.catalog.append({"id": prod_id, "name": name, "price": f"₽ {price}"})
    log.info("Admin %s added product %s (%s ₽)", m.from_user.id, name, price)
    await m.reply(f"Добавлено: {name} — ₽ {price}")

# /delphone id
@router.message(Command("delphone"))
@admin_only
async def del_phone(m: types.Message):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        return await m.reply("Использование: /delphone <id>")

    prod_id = parts[1]
    removed = [p for p in models.catalog if p["id"] == prod_id]
    if not removed:
        log.warning("Admin %s tried to delete unknown id %s", m.from_user.id, prod_id)
        return await m.reply("ID не найден")

    models.catalog[:] = [p for p in models.catalog if p["id"] != prod_id]
    log.info("Admin %s deleted product %s", m.from_user.id, removed[0]["name"])
    await m.reply(f"Удалён {removed[0]['name']}")
