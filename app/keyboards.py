from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from . import models, config


async def catalog_kb() -> InlineKeyboardMarkup:
    """Создаёт inline-клавиатуру с актуальными моделями iPhone."""
    kb = InlineKeyboardBuilder()
    for p in await models.get_catalog():
        kb.add(
            InlineKeyboardButton(
                text = f"{p['model']} — ₽ {p['price']:,}",
                callback_data = f"prod:{p['id']}",
            )
        )
    return kb.as_markup()


def start_kb() -> InlineKeyboardMarkup:
    """Клавиатура для команды /start с кнопкой «Каталог»."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Каталог", callback_data="show_catalog")
    return builder.as_markup()


def simple_kb(values: list, prefix: str, back_cb: str | None = None) -> InlineKeyboardMarkup:
    """"Генерирует клавиатуру со списком значений + кнопка «Назад» (если есть)."""
    kb = InlineKeyboardBuilder()
    for v in values:
        kb.add(InlineKeyboardButton(text=str(v), callback_data=f"{prefix}:{v}"))
    if back_cb:
        kb.row(InlineKeyboardButton(text="◀ Назад", callback_data=back_cb))
    return kb.as_markup()


def paged_kb(values: list, page: int, prefix: str, per_page: int = 6) -> tuple[InlineKeyboardMarkup, int]:
    """Клавиатура с пагинацией: каждая кнопка — в отдельной строке, навигация снизу."""
    pages = (len(values) - 1) // per_page + 1
    page = max(0, min(page, pages - 1))
    start, end = page * per_page, (page + 1) * per_page

    builder = InlineKeyboardBuilder()

    for v in values[start:end]:
        builder.row(  # каждая кнопка — в своём ряду
            InlineKeyboardButton(text=str(v), callback_data=f"{prefix}:{v}")
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"page:{prefix}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"page:{prefix}:{page+1}"))
    if nav:
        builder.row(*nav)

    return builder.as_markup(), page


async def send_product_card(
    msg: Message,
    phone: dict,
    delete_prev: bool = False,
    ask_confirm: bool = False,
) -> None:
    """
    Отправляет карточку товара с описанием.
    Если ask_confirm=True — показывает кнопки «Этот хочу» и «Назад».
    """
    lines = [
        f"*{phone['model']}*",
        f"Память: {phone['storage']} GB" if phone["storage"] else None,
        f"Цвет: {phone['color']}"        if phone["color"]   else None,
        f"Цена: *₽ {phone['price']:,}*",
    ]

    if not ask_confirm:
        lines += ["", "Для заказа свяжитесь с менеджером:", config.MANAGER_CONTACT]

    caption = "\n".join(l for l in lines if l)

    kb = None
    if ask_confirm:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Этот хочу", callback_data=f"buy:{phone['id']}")
        )
        builder.row(
            InlineKeyboardButton(text="❌ Назад", callback_data="back:colors")
        )
        kb = builder.as_markup()

    if phone["photo"]:
        await msg.answer_photo(phone["photo"], caption=caption,reply_markup=kb, parse_mode="Markdown")
    else:
        await msg.answer(caption, reply_markup=kb, parse_mode="Markdown")

    if delete_prev:
        await msg.delete()


class InlineBuilderOneColumn(InlineKeyboardBuilder):
    """Переопределение: каждая кнопка добавляется в отдельную строку."""
    def add(self, *buttons: InlineKeyboardButton) -> None:
        self.row(*buttons)

    def as_markup(self) -> InlineKeyboardMarkup:
        return super().as_markup()
