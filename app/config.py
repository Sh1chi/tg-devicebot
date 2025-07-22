from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x}
DATABASE_URL = os.getenv("DATABASE_URL")

# список ID менеджеров (разрешаем несколько через пробел)
MANAGER_IDS = list(
    map(int, os.getenv("MANAGER_IDS", "").split())
)

# готовая подпись у вас уже есть
MANAGER_CONTACT = (
    f"📞 *Менеджер*: {os.getenv('MANAGER_PHONE')}\n"
    f"✉️ {os.getenv('MANAGER_USERNAME')}"
)
