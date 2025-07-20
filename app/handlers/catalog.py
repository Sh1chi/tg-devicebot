from aiogram import Router, types, F
from .. import models, keyboards, config, logger

router = Router()
log = logger.logging.getLogger(__name__)

@router.callback_query(F.data == "show_catalog")
async def show_catalog(c: types.CallbackQuery):
    log.info("User %s opened catalog", c.from_user.id)
    await c.message.edit_text(
        "Вот что у нас есть сейчас:",
        reply_markup=keyboards.catalog_kb(),
    )
    await c.answer()

@router.callback_query(F.data.startswith("prod:"))
async def product_card(c: types.CallbackQuery):
    prod_id = c.data.split(":", 1)[1]
    product = next((p for p in models.catalog if p["id"] == prod_id), None)
    if not product:
        log.error("Product %s not found (user %s)", prod_id, c.from_user.id)
        return await c.answer("Товар не найден 🤷", show_alert=True)

    log.info('User %s requested product "%s"', c.from_user.id, product["name"])
    await c.message.edit_text(
        f"*{product['name']}*\n"
        f"Цена: *{product['price']}*\n\n"
        "Чтобы оформить заказ свяжитесь с нашим менеджером:\n"
        f"{config.MANAGER_CONTACT}",
        parse_mode="Markdown",
    )
    await c.answer("Контакты менеджера отправлены")
