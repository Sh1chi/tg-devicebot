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
    for uid in await models.all_user_ids():
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