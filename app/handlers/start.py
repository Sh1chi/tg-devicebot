from aiogram import Router, F, types
from aiogram.filters import CommandStart
from .. import models, keyboards, logger

router = Router()
log = logger.logging.getLogger(__name__)

@router.message(CommandStart())
async def cmd_start(m: types.Message):
    models.users.add(m.from_user.id)
    log.info("User %s pressed /start", m.from_user.id)

    await m.answer(
        "Привет! 👋\n"
        "Я помогу подобрать нужный iPhone.\n\n"
        "Нажмите кнопку *«Каталог»* чтобы посмотреть актуальные модели.",
        reply_markup=keyboards.start_kb(),
        parse_mode="Markdown",
    )
