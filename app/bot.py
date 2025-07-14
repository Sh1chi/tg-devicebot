"""
device_bot.py — Telegram-бот (telebot) c рота­ци­он­ны­ми логами
----------------------------------------------------------------
• хранит «каталог» iPhone-ов в памяти;
• показывает каталог и контакты менеджера;
• запоминает пользователей для рассылок;
• админ-команды: /broadcast /addphone /delphone
• логи пишутся в консоль и в logs/bot.log (ротация раз в сутки, хранится 7 дней)
"""

import os, shlex, pathlib, logging
from logging.handlers import TimedRotatingFileHandler
from dotenv import load_dotenv
import telebot
from telebot import types

# ────────────────────────── ЛОГИРОВАНИЕ ──────────────────────────
LOG_DIR = pathlib.Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "bot.log"

FORMAT = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt=DATEFMT,
    handlers=[
        logging.StreamHandler(),                         # → консоль
        TimedRotatingFileHandler(                        # → файл
            LOG_FILE, when="midnight", backupCount=7, encoding="utf-8"
        ),
    ],
)
log = logging.getLogger(__name__)
telebot.logger.setLevel(logging.INFO)  # хотим видеть входящие update-ы

# ───────────────────────────── НАСТРОЙКИ ─────────────────────────
load_dotenv()
BOT_TOKEN      = os.getenv("BOT_TOKEN")
ADMIN_IDS      = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x}
MANAGER_PHONE  = os.getenv("MANAGER_PHONE")
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_CONTACT  = f"📞 *Менеджер*: {MANAGER_PHONE}\n✉️ {MANAGER_USERNAME}"

# ─────────────────────── «БД» В ПАМЯТИ ───────────────────────────
catalog: list[dict] = [
    {"id": "14pro256", "name": "iPhone 14 Pro 256 GB",  "price": "₽ 109 990"},
    {"id": "14pro128", "name": "iPhone 14 Pro 128 GB",  "price": "₽ 99 990"},
    {"id": "13mini128", "name": "iPhone 13 mini 128 GB","price": "₽ 69 990"},
]
users: set[int] = set()

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ─────────────────── ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ─────────────────────
def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def build_catalog_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    for p in catalog:
        kb.add(
            types.InlineKeyboardButton(
                text=f"{p['name']} — {p['price']}",
                callback_data=f"prod:{p['id']}",
            )
        )
    return kb

# ────────────────────────── ХЭНДЛЕРЫ ─────────────────────────────
@bot.message_handler(commands=["start"])
def handle_start(m: types.Message):
    users.add(m.from_user.id)
    log.info("User %s pressed /start", m.from_user.id)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📱 Каталог", callback_data="show_catalog"))

    bot.send_message(
        m.chat.id,
        "Привет! 👋\n"
        "Я помогу подобрать нужный iPhone.\n\n"
        "Нажмите кнопку *«Каталог»* чтобы посмотреть актуальные модели.",
        reply_markup=kb,
    )


@bot.callback_query_handler(func=lambda c: c.data == "show_catalog")
def handle_show_catalog(c: types.CallbackQuery):
    log.info("User %s opened catalog", c.from_user.id)

    bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.id,
        text="Вот что у нас есть сейчас:",
        reply_markup=build_catalog_kb(),
    )
    bot.answer_callback_query(c.id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("prod:"))
def handle_product(c: types.CallbackQuery):
    prod_id = c.data.split(":", 1)[1]
    product = next((p for p in catalog if p["id"] == prod_id), None)

    if not product:
        log.error("Product %s not found (user %s)", prod_id, c.from_user.id)
        bot.answer_callback_query(c.id, "Товар не найден 🤷")
        return

    log.info("User %s requested product \"%s\"", c.from_user.id, product["name"])

    bot.edit_message_text(
        chat_id=c.message.chat.id,
        message_id=c.message.id,
        text=(
            f"*{product['name']}*\n"
            f"Цена: *{product['price']}*\n\n"
            "Чтобы оформить заказ свяжитесь с нашим менеджером:\n"
            f"{MANAGER_CONTACT}"
        ),
    )
    bot.answer_callback_query(c.id, "Контакты менеджера отправлены")

# ──────────────────────── ДЕКОРАТОР АДМИН ─────────────────────────
def admin_only(handler):
    def wrapper(m: types.Message, *args, **kwargs):
        if not is_admin(m.from_user.id):
            log.warning("User %s tried admin cmd %s", m.from_user.id, m.text.split()[0])
            bot.send_message(m.chat.id, "⛔️ Доступ только для админа")
            return
        return handler(m, *args, **kwargs)
    return wrapper

# ────────────────────────── АДМИН-КОМАНДЫ ────────────────────────
@bot.message_handler(commands=["broadcast"])
@admin_only
def cmd_broadcast(m: types.Message):
    if " " not in m.text:
        bot.reply_to(m, "Использование: /broadcast сообщение")
        return
    _, text = m.text.split(" ", 1)

    ok = fail = 0
    for uid in users:
        try:
            bot.send_message(uid, f"🛎️ {text}")
            ok += 1
        except Exception as e:
            fail += 1
            log.exception("Broadcast to %s failed: %s", uid, e)

    log.info("Broadcast by %s: '%s' (ok=%d, fail=%d)", m.from_user.id, text, ok, fail)
    bot.reply_to(m, f"Рассылка завершена ✅: {ok} успешных, {fail} ошибок")


@bot.message_handler(commands=["addphone"])
@admin_only
def cmd_addphone(m: types.Message):
    # разбиваем команду на части, учитывая кавычки
    try:
        parts = shlex.split(m.text, posix=False)
        # должно получиться минимум 4 элемента: ['/addphone', id, 'Название', 'Цена']
        if len(parts) < 4:
            raise ValueError
        _, prod_id, name, price = parts[:4]
    except ValueError:
        bot.reply_to(
            m,
            "Использование:\n"
            "/addphone <id> \"Название модели\" <Цена>\n"
            "Пример:\n"
            "/addphone 15promax512 \"iPhone 15 Pro Max 512 GB\" 149990"
        )
        return

    if any(p["id"] == prod_id for p in catalog):
        bot.reply_to(m, "ID уже существует.")
        log.warning("Admin %s tried to add existing id %s", m.from_user.id, prod_id)
        return

    catalog.append({"id": prod_id, "name": name, "price": f"₽ {price}"})
    log.info("Admin %s added product %s (%s ₽)", m.from_user.id, name, price)
    bot.reply_to(m, f"Добавлено: {name} — ₽ {price}")


@bot.message_handler(commands=["delphone"])
@admin_only
def cmd_delphone(m: types.Message):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(m, "Использование: /delphone <id>")
        return

    prod_id = parts[1]
    removed = [p for p in catalog if p["id"] == prod_id]
    if not removed:
        bot.reply_to(m, "ID не найден")
        log.warning("Admin %s tried to delete unknown id %s", m.from_user.id, prod_id)
        return

    catalog[:] = [p for p in catalog if p["id"] != prod_id]
    log.info("Admin %s deleted product %s", m.from_user.id, removed[0]["name"])
    bot.reply_to(m, f"Удалён {removed[0]['name']}")

# ─────────────────────────── ГЛАВНЫЙ БЛОК ─────────────────────────
if __name__ == "__main__":
    log.info("Bot starting…")
    bot.infinity_polling(skip_pending=True)
