from dotenv import load_dotenv
import os

# Загружаем переменные окружения из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Список Telegram ID администраторов
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x}

# Список Telegram ID менеджеров
MANAGER_IDS = [int(x) for x in os.getenv("MANAGER_IDS", "").split(",") if x]

# Готовая подпись менеджера (телефон + username)
MANAGER_CONTACT = (
    f"📞 *Менеджер*: {os.getenv('MANAGER_PHONE')}\n"
    f"✉️ {os.getenv('MANAGER_USERNAME')}"
)
