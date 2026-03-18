from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot
from config import GROUP_ID
from db import (
    get_user_by_telegram_id,
    get_all_products,
    get_product_by_id,
    create_sale,
    save_location,
    get_agent_daily_sales
)
from keyboards import (
    agent_menu,
    sale_product_kb,
    confirm_sale_kb,
    request_location_kb,
    long_reports_menu
)
from states import AgentSaleState
from utils.helpers import is_number, sale_preview, format_price


def is_agent(message):
    user = get_user_by_telegram_id(message.from_user.id)
    return user and user["role"] == "agent"


@dp.message_handler(lambda message: message.text == "Sotish")
async def sale_start(message: types.Message):
    if not is_agent(message):
        return

    products = get_all_products()
    if not products:
        await message.answer("Mahsulotlar yo'q.")
        return

    await message.answer("Mahsulotni tanlang:", reply_markup=sale_product_kb(products))


@dp.callback_query_handler(lambda c: c.data.startswith("sale_product:"))
async def sale_choose_product(call: types.CallbackQuery, state: FSMContext):
    product_id = int(call.data.split(":")[1])
    product = get_product_by_id(product_id)

    if not product:
        await call.answer("Mahsulot topilmadi", show_alert=True)
        return

    await state.update_data(product_id=product_id)
    await AgentSaleState.waiting_shop_name.set()

    await call.message.answer("Sotayotgan do'kon yoki shahobcha nomini kiriting:")
    await call.answer()


@dp.message_handler(state=AgentSaleState.waiting_shop_name)
async def sale_shop_name(message: types.Message, state: FSMContext):
    await state.update_data(shop_name=message.text.strip())
    await AgentSaleState.waiting_sale_qty.set()
    await message.answer("Mahsulot sonini kiriting:")


@dp.message_handler(state=AgentSaleState.waiting_sale_qty)
async def sale_qty(message: types.Message, state: FSMContext):
    if not is_number(message.text):
        await message.answer("Soni faqat son bo'lishi kerak.")
        return

    qty = int(message.text)
    data = await state.get_data()
    product = get_product_by_id(data["product_id"])

    if not product:
        await message.answer("Mahsulot topilmadi.")
        await state.finish()
        return

    await state.update_data(qty=qty)

    text = sale_preview(
        data["shop_name"],
        product["name"],
        qty,
        product["price"]
    )

    await message.answer(text, reply_markup=confirm_sale_kb())


@dp.callback_query_handler(lambda c: c.data == "sale_cancel", state="*")
async def sale_cancel(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer("Sotuv bekor qilindi.", reply_markup=agent_menu())
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "sale_edit", state="*")
async def sale_edit(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if "product_id" not in data:
        await call.answer("Ma'lumot topilmadi", show_alert=True)
        return

    await AgentSaleState.waiting_shop_name.set()
    await call.message.answer("Do'kon nomini qaytadan kiriting:")
    await call.answer()


@dp.callback_query_handler(lambda c: c.data == "sale_confirm", state="*")
async def sale_confirm(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if "product_id" not in data or "qty" not in data or "shop_name" not in data:
        await call.answer("Ma'lumot yetarli emas", show_alert=True)
        return

    await AgentSaleState.waiting_location.set()
    await call.message.answer(
        "Sotuvni yakunlash uchun lokatsiyani yuboring.",
        reply_markup=request_location_kb()
    )
    await call.answer()


@dp.message_handler(content_types=types.ContentType.LOCATION, state=AgentSaleState.waiting_location)
async def receive_location_and_finish_sale(message: types.Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user or user["role"] != "agent":
        await state.finish()
        return

    data = await state.get_data()
    product = get_product_by_id(data["product_id"])

    if not product:
        await message.answer("Mahsulot topilmadi.", reply_markup=agent_menu())
        await state.finish()
        return

    result = create_sale(
        agent_id=user["id"],
        product_id=product["id"],
        shop_name=data["shop_name"],
        quantity=data["qty"],
        unit_price=product["price"]
    )

    if not result["ok"]:
        await message.answer(result["message"], reply_markup=agent_menu())
        await state.finish()
        return

    save_location(
        sale_id=result["sale_id"],
        agent_id=user["id"],
        latitude=message.location.latitude,
        longitude=message.location.longitude
    )

    sale_text = (
        "✅ Sotuv tasdiqlandi\n"
        "Agent: {0}\n"
        "Do'kon: {1}\n"
        "Mahsulot: {2}\n"
        "Soni: {3}\n"
        "Narxi: {4}\n"
        "Jami: {5}"
    ).format(
        user["full_name"],
        data["shop_name"],
        product["name"],
        data["qty"],
        format_price(product["price"]),
        format_price(result["total_price"])
    )

    await bot.send_message(GROUP_ID, sale_text)
    await bot.send_location(
        GROUP_ID,
        latitude=message.location.latitude,
        longitude=message.location.longitude
    )

    await message.answer("Sotuv va lokatsiya yuborildi.", reply_markup=agent_menu())
    await state.finish()


@dp.message_handler(lambda message: message.text == "Hisobot (kunlik)")
async def daily_report_handler(message: types.Message):
    if not is_agent(message):
        return

    user = get_user_by_telegram_id(message.from_user.id)
    sales = get_agent_daily_sales(user["id"])

    if not sales:
        await message.answer("Bugun sotuvlar yo'q.")
        return

    lines = []
    total_sum = 0

    for sale in sales:
        total_sum += int(sale["total_price"])
        lines.append(
            "{0}: {1} x {2} = {3}".format(
                sale["product_name"],
                sale["quantity"],
                format_price(sale["unit_price"]),
                format_price(sale["total_price"])
            )
        )

    lines.append("")
    lines.append("Jami: {0}".format(format_price(total_sum)))

    await message.answer("\n".join(lines))


@dp.message_handler(lambda message: message.text == "Hisobot (uzoq muddatlik)")
async def long_report_handler(message: types.Message):
    if not is_agent(message):
        return
    await message.answer("Davrni tanlang:", reply_markup=long_reports_menu())


@dp.message_handler(lambda message: message.text in ["Kunlik", "Haftalik", "Yillik"])
async def period_report_handler(message: types.Message):
    if not is_agent(message):
        return
    await message.answer("Bu bo'limni keyingi qadamda to'ldiramiz.", reply_markup=agent_menu())


@dp.message_handler(lambda message: message.text == "Ortga")
async def agent_back_handler(message: types.Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    if user["role"] == "agent":
        await message.answer("Asosiy menyu", reply_markup=agent_menu())