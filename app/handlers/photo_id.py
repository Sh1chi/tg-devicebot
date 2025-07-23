from aiogram import Router, F, types
from aiogram.filters import StateFilter

from .. import config, logger

router = Router()
ADMINS = set(config.ADMIN_IDS)
log = logger.logging.getLogger(__name__)

@router.message(StateFilter(None), F.photo)        # срабатывает ТОЛЬКО вне FSM
async def send_file_id(m: types.Message) -> None:
    """Админ прислал фото → шлём ему file_id."""
    if m.from_user.id not in ADMINS:               # безопасность
        return

    file_id = m.photo[-1].file_id                 # последняя = самое большое разрешение
    reply = (
        "🆔 *file_id*\n"
        f"`{file_id}`\n\n"
        "_Сохрани этот идентификатор и вставь его в поле `photo` нужного товара._"
    )
    await m.answer(reply, parse_mode="Markdown")
    log.info("Sent file_id to admin %s: %s", m.from_user.id, file_id)
