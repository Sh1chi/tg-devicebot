import pathlib, logging
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = pathlib.Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "bot.log"

FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"

def setup_logging(level: int = logging.INFO):
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
