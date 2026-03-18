from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart

from db import get_user_by_login, bind_telegram_to_user
from keyboards import admin_menu, agent_menu
from services.auth import verify_password

from handlers.loader import dp
from states import LoginState


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message, state: FSMContext):
    await state.finish()
    await LoginState.waiting_login.set()
    await message.answer("Login kiriting:")


@dp.message_handler(state=LoginState.waiting_login)
async def process_login(message: types.Message, state: FSMContext):
    login = message.text.strip()
    await state.update_data(login=login)
    await LoginState.waiting_password.set()
    await message.answer("Parol kiriting:")


@dp.message_handler(state=LoginState.waiting_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    login = data.get("login")

    user = get_user_by_login(login)

    if not user:
        await message.answer("Login topilmadi. Qaytadan /start bosing.")
        await state.finish()
        return

    if int(user["is_active"]) != 1:
        await message.answer("Foydalanuvchi faol emas.")
        await state.finish()
        return

    if not verify_password(password, user["password_hash"]):
        await message.answer("Parol noto'g'ri. Qaytadan /start bosing.")
        await state.finish()
        return

    bind_telegram_to_user(
        user_id=user["id"],
        telegram_id=message.from_user.id,
        username=message.from_user.username
    )

    await state.finish()

    if user["role"] == "admin":
        await message.answer("Xush kelibsiz, admin.", reply_markup=admin_menu())
    else:
        await message.answer("Xush kelibsiz, agent.", reply_markup=agent_menu())