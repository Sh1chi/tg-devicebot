import pathlib, logging

from logging.handlers import TimedRotatingFileHandler

# Путь к папке и файлу логов
LOG_DIR = pathlib.Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "bot.log"

# Формат и дата для лог-сообщений
FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO):
    """Настраивает логирование: консоль + файл с ротацией раз в сутки."""
    logging.basicConfig(
        level=level,
        format=FORMAT,
        datefmt=DATEFMT,
        handlers=[
            logging.StreamHandler(),
            TimedRotatingFileHandler(
                LOG_FILE, when="midnight", backupCount=7, encoding="utf-8"
            ),
        ],
    )
