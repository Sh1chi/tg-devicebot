from __future__ import annotations
from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .. import models, keyboards, config, logger

router = Router()
log = logger.logging.getLogger(__name__)

MANAGERS = config.MANAGER_IDS        # список telegram-id менеджеров


class Catalog(StatesGroup):
    """Состояния выбора модели/памяти/цвета и подтверждения покупки."""
    choosing_model = State()
    choosing_storage = State()
    choosing_color = State()
    confirming_buy = State()


@router.callback_query(F.data == "show_catalog")
async def wizard_entry(c: types.CallbackQuery, state: FSMContext) -> None:
    """Старт мастера выбора модели."""
    await state.clear()
    await state.set_state(Catalog.choosing_model)
    await send_model_step(c.message, page=0)
    await c.answer()


async def send_model_step(msg: types.Message, page: int) -> None:
    """Показывает клавиатуру с выбором модели (постранично)."""
    models_list = await models.distinct_models()
    kb, page = keyboards.paged_kb(models_list, page, prefix="model")
    await msg.edit_text("📱 *Выберите модель:*", reply_markup=kb)


@router.callback_query(
    Catalog.choosing_model,                    # <— состояние
    F.data.startswith("model:")               # <— фильтр на callback_data
)
async def model_chosen(c: types.CallbackQuery, state: FSMContext) -> None:
    """Переход к выбору объёма памяти."""
    model = c.data.split(":", 1)[1]
    await state.update_data(model=model)
    await state.set_state(Catalog.choosing_storage)
    await send_storage_step(c.message, model)
    await c.answer()


async def send_storage_step(msg: types.Message, model: str) -> None:
    """Показывает клавиатуру с доступными объёмами памяти."""
    sizes = await models.distinct_storages(model)
    kb = keyboards.simple_kb(sizes, prefix="storage", back_cb="back:models")
    await msg.edit_text(f"💾 *Память для {model}:*", reply_markup=kb)


@router.callback_query(
    Catalog.choosing_storage,
    F.data.startswith("storage:")
)
async def storage_chosen(c: types.CallbackQuery, state: FSMContext) -> None:
    """Переход к выбору цвета."""
    storage = int(c.data.split(":", 1)[1])
    await state.update_data(storage=storage)
    data = await state.get_data()
    await state.set_state(Catalog.choosing_color)
    await send_color_step(c.message, data["model"], storage)
    await c.answer()


async def send_color_step(msg: types.Message, model: str, storage: int) -> None:
    """Показывает клавиатуру с доступными цветами."""
    colors = await models.distinct_colors(model, storage)
    kb = keyboards.simple_kb(colors, prefix="color", back_cb="back:storages")
    await msg.edit_text(f"🎨 *Цвет* {storage} GB, {model}:", reply_markup=kb)


@router.callback_query(
    Catalog.choosing_color,
    F.data.startswith("color:")
)
async def color_chosen(c: types.CallbackQuery, state: FSMContext) -> None:
    """Показывает карточку товара и кнопки подтверждения."""
    color = c.data.split(":", 1)[1]
    data = await state.update_data(color=color)
    phone = await models.get_phone_by_attrs(**data)

    await keyboards.send_product_card(
        c.message,
        phone,
        delete_prev=True,
        ask_confirm=True,
    )

    await state.set_state(Catalog.confirming_buy)
    await c.answer()


@router.callback_query(Catalog.confirming_buy, F.data.startswith("buy:"))
async def buy_confirmed(c: types.CallbackQuery, state: FSMContext):
    """Обработка нажатия кнопки «Этот хочу» и уведомление менеджеров."""
    phone_id = int(c.data.split(":", 1)[1])
    phone = await models.get_phone(phone_id)

    await c.message.delete()

    final_text = (
        "✅ Спасибо! Наш менеджер скоро свяжется с вами.\n"
        f"{config.MANAGER_CONTACT}"
    )
    await c.message.answer(final_text, parse_mode="Markdown")
    await c.answer("Заказ принят!", show_alert=True)

    log.info("Notifying managers: %s", config.MANAGER_IDS)

    user = c.from_user
    notify_text = (
        "🛒 *Новый заказ!*\n"
        f"Имя: {user.full_name}\n"
        f"ID: `{user.id}`\n"
        f"Модель: {phone['model']}, {phone['storage']} GB, {phone['color']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✉️ Написать клиенту",
                url=f"tg://user?id={user.id}"
            )
        ]
    ])
    for mgr_id in config.MANAGER_IDS:
        try:
            await c.bot.send_message(
                mgr_id,
                notify_text,
                parse_mode="Markdown",
                reply_markup=kb,
            )
        except Exception as e:
            log.error("Cannot notify manager %s: %s", mgr_id, e)

    await state.clear()


@router.callback_query(Catalog.confirming_buy, F.data == "back:colors")
async def back_to_colors(c: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору цвета."""
    data = await state.get_data()
    await state.set_state(Catalog.choosing_color)
    await send_color_step(c.message, data["model"], data["storage"])
    await c.answer()


@router.callback_query(Catalog.choosing_storage, F.data == "back:models")
async def back_to_models(c: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору модели."""
    await state.set_state(Catalog.choosing_model)
    await send_model_step(c.message, page=0)
    await c.answer()


@router.callback_query(Catalog.choosing_color, F.data == "back:storages")
async def back_to_storages(c: types.CallbackQuery, state: FSMContext):
    """Возврат к выбору объёма памяти."""
    data = await state.get_data()
    await state.set_state(Catalog.choosing_storage)
    await send_storage_step(c.message, data["model"])
    await c.answer()


@router.callback_query(F.data == "show_all")
async def show_full_catalog(c: types.CallbackQuery, state: FSMContext) -> None:
    """Показать весь каталог без мастера выбора."""
    await state.clear()
    kb = await keyboards.catalog_kb()
    await c.message.edit_text(
        "Вот что у нас есть сейчас:",
        reply_markup=kb,
    )
    await c.answer()