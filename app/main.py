import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app import config, logger
from app.handlers import routers
from app.logger import setup_logging

async def main():
    setup_logging()
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="Markdown")
    )
    dp = Dispatcher()

    # Подключаем все роутеры
    for r in routers:
        dp.include_router(r)

    try:
        logger.logging.getLogger(__name__).info("Bot starting…")
        await dp.start_polling(bot, skip_updates=True)
    except asyncio.CancelledError:
        # gracefully ignore internal cancellation
        pass
    finally:
        # обязательно закроем сессию у бота
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
