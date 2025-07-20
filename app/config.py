from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x}

MANAGER_CONTACT = (
    f"📞 *Менеджер*: {os.getenv('MANAGER_PHONE')}\n"
    f"✉️ {os.getenv('MANAGER_USERNAME')}"
)
