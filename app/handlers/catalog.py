from aiogram import Router, types, F

from .. import models, keyboards, config, logger

router = Router()
log = logger.logging.getLogger(__name__)


@router.callback_query(F.data == "show_catalog")
async def show_catalog(c: types.CallbackQuery) -> None:
    log.info("User %s opened catalog", c.from_user.id)

    # клавиатура теперь асинхронная: берёт товары из таблицы phones
    kb = await keyboards.catalog_kb()

    await c.message.edit_text(
        "Вот что у нас есть сейчас:",
        reply_markup=kb,
    )
    await c.answer()


@router.callback_query(F.data.startswith("prod:"))
async def product_card(c: types.CallbackQuery) -> None:
    prod_id = c.data.split(":", 1)[1]

    # ищем товар в БД
    product = await models.get_phone(prod_id)
    if not product:
        log.error("Product %s not found (user %s)", prod_id, c.from_user.id)
        return await c.answer("Товар не найден 🤷", show_alert=True)

    log.info('User %s requested product "%s"', c.from_user.id, product["model"])

    # сохраняем интерес пользователя
    await models.add_user_phone(c.from_user.id, prod_id)

    text_parts = [
        f"*{product['model']}*",
        f"Память: {product['storage']} GB" if product["storage"] else None,
        f"Цвет: {product['color']}" if product["color"] else None,
        f"Цена: *₽ {product['price']:,}*",
        "",
        "Чтобы оформить заказ свяжитесь с нашим менеджером:",
        f"{config.MANAGER_CONTACT}",
    ]
    caption = "\n".join(p for p in text_parts if p is not None)

    # Если есть фото — отправим новым сообщением
    if product["photo"]:
        await c.message.answer_photo(
            photo=product["photo"],
            caption=caption,
            parse_mode="Markdown",
        )
        await c.message.delete()  # удалим старую карточку без фото
    else:
        await c.message.edit_text(caption, parse_mode="Markdown")

    await c.answer("Контакты менеджера отправлены")
