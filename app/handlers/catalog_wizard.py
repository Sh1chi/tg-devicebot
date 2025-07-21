from aiogram import Router, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton

from .. import models, keyboards, config, logger

router = Router()
log = logger.logging.getLogger(__name__)


class Catalog(StatesGroup):
    choosing_model   = State()
    choosing_storage = State()
    choosing_color   = State()


@router.callback_query(F.data == "show_catalog")
async def wizard_entry(c: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Catalog.choosing_model)
    await send_model_step(c.message, page=0)
    await c.answer()


async def send_model_step(msg: types.Message, page: int) -> None:
    models_list = await models.distinct_models()
    kb, page = keyboards.paged_kb(models_list, page, prefix="model")

    # ─── после того как получили InlineKeyboardMarkup, дополним её:
    if page == 0:
        # добавляем новую строку с одной кнопкой
        kb.inline_keyboard.append([
            InlineKeyboardButton(text="⏩ Показать всё", callback_data="show_all")
        ])

    await msg.edit_text("📱 *Выберите модель:*", reply_markup=kb)


@router.callback_query(
    Catalog.choosing_model,                    # <— состояние
    F.data.startswith("model:")               # <— фильтр на callback_data
)
async def model_chosen(c: types.CallbackQuery, state: FSMContext) -> None:
    model = c.data.split(":", 1)[1]
    await state.update_data(model=model)
    await state.set_state(Catalog.choosing_storage)
    await send_storage_step(c.message, model)
    await c.answer()


async def send_storage_step(msg: types.Message, model: str) -> None:
    sizes = await models.distinct_storages(model)
    kb = keyboards.simple_kb(sizes, prefix="storage", back_cb="back:models")
    await msg.edit_text(f"💾 *Память для {model}:*", reply_markup=kb)


@router.callback_query(
    Catalog.choosing_storage,
    F.data.startswith("storage:")
)
async def storage_chosen(c: types.CallbackQuery, state: FSMContext) -> None:
    storage = int(c.data.split(":", 1)[1])
    await state.update_data(storage=storage)
    data = await state.get_data()
    await state.set_state(Catalog.choosing_color)
    await send_color_step(c.message, data["model"], storage)
    await c.answer()


async def send_color_step(msg: types.Message, model: str, storage: int) -> None:
    colors = await models.distinct_colors(model, storage)
    kb = keyboards.simple_kb(colors, prefix="color", back_cb="back:storages")
    await msg.edit_text(f"🎨 *Цвет* {storage} GB, {model}:", reply_markup=kb)


@router.callback_query(
    Catalog.choosing_color,
    F.data.startswith("color:")
)
async def color_chosen(c: types.CallbackQuery, state: FSMContext) -> None:
    color = c.data.split(":", 1)[1]
    data = await state.update_data(color=color)
    phone = await models.get_phone_by_attrs(**data)
    await state.clear()
    await keyboards.send_product_card(c.message, phone, delete_prev=True)
    await models.add_user_phone(c.from_user.id, phone["id"])
    await c.answer("Контакты менеджера отправлены")


@router.callback_query(Catalog.choosing_storage, F.data == "back:models")
async def back_to_models(c: types.CallbackQuery, state: FSMContext):
    await state.set_state(Catalog.choosing_model)
    await send_model_step(c.message, page=0)
    await c.answer()


@router.callback_query(Catalog.choosing_color, F.data == "back:storages")
async def back_to_storages(c: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(Catalog.choosing_storage)
    await send_storage_step(c.message, data["model"])
    await c.answer()


@router.callback_query(F.data == "show_all")
async def show_full_catalog(c: types.CallbackQuery, state: FSMContext) -> None:
    # выходим из мастера, показываем полный каталог
    await state.clear()
    kb = await keyboards.catalog_kb()
    await c.message.edit_text(
        "Вот что у нас есть сейчас:",
        reply_markup=kb,
    )
    await c.answer()