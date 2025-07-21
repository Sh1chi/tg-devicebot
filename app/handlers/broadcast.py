from __future__ import annotations
import asyncio
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton

from .. import models, keyboards, logger, config

router = Router()
log = logger.logging.getLogger(__name__)

ADMINS = set(config.ADMIN_IDS)          # телеграм-id ваших админов


# ─────────── FSM ───────────
class BC(StatesGroup):
    choosing_audience = State()
    typing_text       = State()
    waiting_photo     = State()
    confirming        = State()


# ─────────── /broadcast ───────────
@router.message(F.text == "/broadcast")
async def broadcast_entry(m: types.Message, state: FSMContext):
    if m.from_user.id not in ADMINS:
        return
    await state.clear()

    # клавиатура: «📢 Всем» + список моделей iPhone
    kb = await build_audience_kb()
    await m.answer("Кому отправлять рассылку?", reply_markup=kb)
    await state.set_state(BC.choosing_audience)


async def build_audience_kb() -> types.InlineKeyboardMarkup:
    models_list = await models.distinct_models()
    builder = keyboards.InlineBuilderOneColumn()

    # «📢 Всем»
    builder.add(InlineKeyboardButton(text="📢 Всем", callback_data="aud:all"))

    # по моделям
    for mdl in models_list:
        builder.add(InlineKeyboardButton(text=mdl, callback_data=f"aud:{mdl}"))

    return builder.as_markup()


# ─────────── Шаг 0: выбор аудитории ───────────
@router.callback_query(BC.choosing_audience, F.data.startswith("aud:"))
async def aud_chosen(c: types.CallbackQuery, state: FSMContext):
    key = c.data.split(":", 1)[1]          # 'all' или 'iPhone 14 Plus'
    await state.update_data(
        audience="all" if key == "all" else key
    )
    await state.set_state(BC.typing_text)
    txt = "✏️ Пришлите текст рассылки:"
    if key == "all":
        txt = "📢 *Всем пользователям.*\n\n" + txt
    else:
        txt = f"📢 *Тем, кто интересовался {key}.*\n\n" + txt
    await c.message.edit_text(txt, parse_mode="Markdown")
    await c.answer()


# ─────────── Шаг 1: текст ───────────
@router.message(BC.typing_text, F.text)
async def txt_received(m: types.Message, state: FSMContext):
    await state.update_data(text=m.text)
    await state.set_state(BC.waiting_photo)
    await m.answer("🖼 Если нужна картинка — пришлите ее.\nОтправьте /skip, чтобы продолжить без фото.")


# ─────────── Шаг 2: фото или /skip ───────────
@router.message(BC.waiting_photo, F.photo)
async def photo_received(m: types.Message, state: FSMContext):
    file_id = m.photo[-1].file_id
    await state.update_data(photo=file_id)
    await ask_confirm(m, state)


@router.message(BC.waiting_photo, F.text == "/skip")
async def skip_photo(m: types.Message, state: FSMContext):
    await ask_confirm(m, state)


async def ask_confirm(msg: types.Message | types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    builder = keyboards.InlineBuilderOneColumn()
    builder.add(InlineKeyboardButton(text="✅ Отправить", callback_data="bc:send"))
    builder.add(InlineKeyboardButton(text="❌ Отмена",   callback_data="bc:cancel"))

    preview = data["text"]
    if data.get("photo"):
        await msg.answer_photo(data["photo"], caption=preview, reply_markup=builder.as_markup())
    else:
        await msg.answer(preview, reply_markup=builder.as_markup())
    await state.set_state(BC.confirming)


# ─────────── Шаг 3: подтверждение ───────────
@router.callback_query(BC.confirming, F.data == "bc:send")
async def do_broadcast(c: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await c.answer("Рассылка запущена!", show_alert=True)
    await state.clear()

    # 1) собираем список получателей
    if data["audience"] == "all":
        users = await models.all_user_ids()
    else:
        users = await models.user_ids_for_model(data["audience"])

    # 2) рассылаем
    sent, failed = 0, 0
    for uid in users:
        try:
            if data.get("photo"):
                await c.bot.send_photo(uid, data["photo"], caption=data["text"])
            else:
                await c.bot.send_message(uid, data["text"])
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.07)       # анти-флуд

    log.info("Broadcast done: sent=%s failed=%s", sent, failed)
    await c.message.answer(f"✅ Рассылка завершена.\nОтправлено: {sent}\nНе доставлено: {failed}")


@router.callback_query(BC.confirming, F.data == "bc:cancel")
async def bc_cancel(c: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text("🚫 Рассылка отменена.")
    await c.answer()
