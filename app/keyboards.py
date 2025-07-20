from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from . import models

def catalog_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for p in models.catalog:
        kb.add(
            InlineKeyboardButton(
                text=f"{p['name']} — {p['price']}",
                callback_data=f"prod:{p['id']}",
            )
        )
    return kb.as_markup()

def start_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Каталог", callback_data="show_catalog")
    return builder.as_markup()
