from aiogram import Router, types, F          # F пока не используется, но оставлен «как было»
from aiogram.filters import CommandStart

from .. import models, keyboards, logger

router = Router()
log = logger.logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(m: types.Message) -> None:
    # вместо in-memory set сохраняем пользователя в таблицу users
    await models.save_user(
        tg_id=m.from_user.id,
        username=m.from_user.username,
        first=m.from_user.first_name,
    )
    log.info("User %s pressed /start", m.from_user.id)

    await m.answer(
        "Привет! 👋\n"
        "Я помогу подобрать нужный iPhone.\n\n"
        "Нажмите кнопку *«Каталог»* чтобы посмотреть актуальные модели.",
        reply_markup=keyboards.start_kb(),
        parse_mode="Markdown",
    )
