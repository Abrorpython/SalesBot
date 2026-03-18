from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp
from db import (
    get_user_by_telegram_id,
    create_product,
    get_all_products,
    get_product_by_id,
    update_product,
    delete_product,
    add_stock,
    get_stock_report,
    create_user,
    get_all_agents
)
from keyboards import (
    admin_menu,
    products_menu,
    agents_menu,
    reports_menu,
    product_list_kb,
    product_action_kb,
    stock_product_kb
)
from states import AdminProductState, AdminStockState, AdminAgentState
from utils.auth import hash_password
from utils.helpers import is_number, format_price


def is_admin(message):
    user = get_user_by_telegram_id(message.from_user.id)
    return user and user["role"] == "admin"


@dp.message_handler(lambda message: message.text == "Mahsulotlar")
async def products_menu_handler(message: types.Message):
    if not is_admin(message):
        return
    await message.answer("Mahsulotlar bo'limi", reply_markup=products_menu())


@dp.message_handler(lambda message: message.text == "Agentlar")
async def agents_menu_handler(message: types.Message):
    if not is_admin(message):
        return
    await message.answer("Agentlar bo'limi", reply_markup=agents_menu())


@dp.message_handler(lambda message: message.text == "Hisobotlar")
async def reports_handler(message: types.Message):
    if not is_admin(message):
        return
    await message.answer("Hisobotlar", reply_markup=reports_menu())


@dp.message_handler(lambda message: message.text == "Mahsulot qo'shish")
async def add_product_start(message: types.Message):
    if not is_admin(message):
        return
    await AdminProductState.waiting_product_name.set()
    await message.answer("Mahsulot nomini kiriting:")


@dp.message_handler(state=AdminProductState.waiting_product_name)
async def add_product_name(message: types.Message, state: FSMContext):
    await state.update_data(product_name=message.text.strip())
    await AdminProductState.waiting_product_price.set()
    await message.answer("Mahsulot narxini kiriting:")


@dp.message_handler(state=AdminProductState.waiting_product_price)
async def add_product_price(message: types.Message, state: FSMContext):
    if not is_number(message.text):
        await message.answer("Narx faqat son bo'lishi kerak.")
        return

    data = await state.get_data()
    name = data["product_name"]
    price = int(message.text)

    try:
        create_product(name, price)
        await message.answer("Mahsulot qo'shildi.", reply_markup=products_menu())
    except Exception as e:
        await message.answer("Xatolik: {0}".format(str(e)))

    await state.finish()


@dp.message_handler(lambda message: message.text == "Mahsulot ro'yxati")
async def product_list_handler(message: types.Message):
    if not is_admin(message):
        return

    products = get_all_products()
    if not products:
        await message.answer("Mahsulotlar yo'q.")
        return

    await message.answer("Mahsulotlar:", reply_markup=product_list_kb(products))


@dp.callback_query_handler(lambda c: c.data.startswith("product_view:"))
async def product_view_handler(call: types.CallbackQuery):
    product_id = int(call.data.split(":")[1])
    product = get_product_by_id(product_id)

    if not product:
        await call.answer("Mahsulot topilmadi", show_alert=True)
        return

    text = (
        "Mahsulot: {0}\n"
        "Narxi: {1}\n"
        "Soni: {2} ta"
    ).format(
        product["name"],
        format_price(product["price"]),
        product["quantity"]
    )

    await call.message.answer(text, reply_markup=product_action_kb(product_id))
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("product_delete:"))
async def product_delete_handler(call: types.CallbackQuery):
    product_id = int(call.data.split(":")[1])
    delete_product(product_id)
    await call.message.answer("Mahsulot o'chirildi.")
    await call.answer()


@dp.callback_query_handler(lambda c: c.data.startswith("product_edit:"))
async def product_edit_start(call: types.CallbackQuery, state: FSMContext):
    product_id = int(call.data.split(":")[1])
    product = get_product_by_id(product_id)

    if not product:
        await call.answer("Mahsulot topilmadi", show_alert=True)
        return

    await state.update_data(edit_product_id=product_id)
    await AdminProductState.waiting_edit_product_name.set()
    await call.message.answer("Yangi mahsulot nomini kiriting:")
    await call.answer()


@dp.message_handler(state=AdminProductState.waiting_edit_product_name)
async def product_edit_name(message: types.Message, state: FSMContext):
    await state.update_data(edit_product_name=message.text.strip())
    await AdminProductState.waiting_edit_product_price.set()
    await message.answer("Yangi mahsulot narxini kiriting:")


@dp.message_handler(state=AdminProductState.waiting_edit_product_price)
async def product_edit_price(message: types.Message, state: FSMContext):
    if not is_number(message.text):
        await message.answer("Narx son bo'lishi kerak.")
        return

    data = await state.get_data()
    product_id = data["edit_product_id"]
    name = data["edit_product_name"]
    price = int(message.text)

    update_product(product_id, name, price)
    await message.answer("Mahsulot tahrirlandi.", reply_markup=products_menu())
    await state.finish()


@dp.message_handler(lambda message: message.text == "Ombor")
async def stock_start(message: types.Message):
    if not is_admin(message):
        return

    products = get_all_products()
    if not products:
        await message.answer("Mahsulotlar yo'q.")
        return

    await message.answer("Qaysi mahsulotga qo'shasiz?", reply_markup=stock_product_kb(products))


@dp.callback_query_handler(lambda c: c.data.startswith("stock_add:"))
async def stock_choose_product(call: types.CallbackQuery, state: FSMContext):
    product_id = int(call.data.split(":")[1])
    await state.update_data(stock_product_id=product_id)
    await AdminStockState.waiting_stock_qty.set()
    await call.message.answer("Nechta kelganligini kiriting:")
    await call.answer()


@dp.message_handler(state=AdminStockState.waiting_stock_qty)
async def stock_qty_handler(message: types.Message, state: FSMContext):
    if not is_number(message.text):
        await message.answer("Soni faqat son bo'lishi kerak.")
        return

    qty = int(message.text)
    data = await state.get_data()
    product_id = data["stock_product_id"]

    user = get_user_by_telegram_id(message.from_user.id)
    total_qty = add_stock(product_id, qty, user["id"])

    if total_qty is None:
        await message.answer("Mahsulot topilmadi.")
        await state.finish()
        return

    await message.answer(
        "Qabul qilindi.\nJami: {0} ta".format(total_qty),
        reply_markup=admin_menu()
    )
    await state.finish()


@dp.message_handler(lambda message: message.text == "Real hisobot")
async def real_report_handler(message: types.Message):
    if not is_admin(message):
        return

    products = get_stock_report()
    if not products:
        await message.answer("Mahsulotlar yo'q.")
        return

    lines = []
    grand_total = 0

    for item in products:
        total = int(item["quantity"]) * int(item["price"])
        grand_total += total
        lines.append(
            "{0}: {1} x {2} = {3}".format(
                item["name"],
                item["quantity"],
                format_price(item["price"]),
                format_price(total)
            )
        )

    lines.append("")
    lines.append("Umumiy summa: {0}".format(format_price(grand_total)))

    await message.answer("\n".join(lines))


@dp.message_handler(lambda message: message.text == "Agent qo'shish")
async def add_agent_start(message: types.Message):
    if not is_admin(message):
        return
    await AdminAgentState.waiting_agent_full_name.set()
    await message.answer("Agent to'liq ismini kiriting:")


@dp.message_handler(state=AdminAgentState.waiting_agent_full_name)
async def add_agent_name(message: types.Message, state: FSMContext):
    await state.update_data(agent_full_name=message.text.strip())
    await AdminAgentState.waiting_agent_login.set()
    await message.answer("Agent login kiriting:")


@dp.message_handler(state=AdminAgentState.waiting_agent_login)
async def add_agent_login(message: types.Message, state: FSMContext):
    await state.update_data(agent_login=message.text.strip())
    await AdminAgentState.waiting_agent_password.set()
    await message.answer("Agent parolini kiriting:")


@dp.message_handler(state=AdminAgentState.waiting_agent_password)
async def add_agent_password(message: types.Message, state: FSMContext):
    data = await state.get_data()

    full_name = data["agent_full_name"]
    login = data["agent_login"]
    password = message.text.strip()

    try:
        create_user(
            full_name=full_name,
            role="agent",
            login=login,
            password_hash=hash_password(password)
        )
        await message.answer("Agent qo'shildi.", reply_markup=agents_menu())
    except Exception as e:
        await message.answer("Xatolik: {0}".format(str(e)))

    await state.finish()


@dp.message_handler(lambda message: message.text == "Agent ro'yxati")
async def agent_list_handler(message: types.Message):
    if not is_admin(message):
        return

    agents = get_all_agents()
    if not agents:
        await message.answer("Agentlar yo'q.")
        return

    lines = ["Agentlar ro'yxati:"]
    for i, agent in enumerate(agents, 1):
        lines.append("{0}. {1} | {2}".format(i, agent["full_name"], agent["login"]))

    await message.answer("\n".join(lines))


@dp.message_handler(lambda message: message.text == "Ortga")
async def admin_back_handler(message: types.Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        return

    if user["role"] == "admin":
        await message.answer("Asosiy menyu", reply_markup=admin_menu())