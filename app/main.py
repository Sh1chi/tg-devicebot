import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app import config, logger, db
from app.handlers import routers
from app.logger import setup_logging


async def main():
    setup_logging()  # Настройка логирования (в файл и консоль)

    await db.connect()  # Подключение к базе данных

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="Markdown") # Используем Markdown-разметку по умолчанию
    )
    dp = Dispatcher()

    # Регистрируем все маршрутизаторы (обработчики событий)
    for r in routers:
        dp.include_router(r)

    try:
        logger.logging.getLogger(__name__).info("Bot starting…")
        await dp.start_polling(bot, skip_updates=True)
    except asyncio.CancelledError:
        # Игнорируем отмену при завершении (например, Ctrl+C)
        pass
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
