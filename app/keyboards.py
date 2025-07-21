from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from . import models, config


async def catalog_kb() -> InlineKeyboardMarkup:
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
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Каталог", callback_data="show_catalog")
    return builder.as_markup()


# ─── облегчённые КБ ──────────────────────────────────────────────
def simple_kb(values: list, prefix: str, back_cb: str | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for v in values:
        kb.add(InlineKeyboardButton(text=str(v), callback_data=f"{prefix}:{v}"))
    if back_cb:
        kb.row(InlineKeyboardButton(text="◀ Назад", callback_data=back_cb))
    return kb.as_markup()


def paged_kb(values: list, page: int, prefix: str, per_page: int = 6) -> tuple[InlineKeyboardMarkup, int]:
    pages = (len(values) - 1) // per_page + 1
    page = max(0, min(page, pages - 1))
    start, end = page * per_page, (page + 1) * per_page

    # теперь одна кнопка в ряду
    builder = InlineKeyboardBuilder()

    for v in values[start:end]:
        builder.row(  # каждая кнопка — в своём ряду
            InlineKeyboardButton(text=str(v), callback_data=f"{prefix}:{v}")
        )

    # пагинация (тоже в одну строку)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀", callback_data=f"page:{prefix}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="▶", callback_data=f"page:{prefix}:{page+1}"))
    if nav:
        # несмотря на row_width, разметка из одного .row() будет в одной строке
        builder.row(*nav)

    return builder.as_markup(), page


# ─── отправка карточки товара ───────────────────────────────────
async def send_product_card(
msg: Message, phone: dict, delete_prev: bool = False
) -> None:
    caption = "\n".join(
        p for p in [
            f"*{phone['model']}*",
            f"Память: {phone['storage']} GB" if phone["storage"] else None,
            f"Цвет: {phone['color']}"       if phone["color"]   else None,
            f"Цена: *₽ {phone['price']:,}*",
            "",
            "Чтобы оформить заказ свяжитесь с нашим менеджером:",
            config.MANAGER_CONTACT,
        ] if p
    )
    if phone["photo"]:
        await msg.answer_photo(phone["photo"], caption=caption, parse_mode="Markdown")
    else:
        await msg.answer(caption, parse_mode="Markdown")
    if delete_prev:
        await msg.delete()


class InlineBuilderOneColumn(InlineKeyboardBuilder):
    """
    Каждую кнопку кладёт на свою строку.
    """
    def add(self, *buttons: InlineKeyboardButton) -> None:  # type: ignore[override]
        # каждая add = новая строка
        self.row(*buttons)

    def as_markup(self) -> InlineKeyboardMarkup:            # noqa: D401
        return super().as_markup()
