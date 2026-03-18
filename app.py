from aiogram import executor

from db import init_db, get_user_by_login, create_user
from handlers import start
from handlers import admin
from handlers import agent
from loader import dp
from utils.auth import hash_password


def create_default_admin():
    admin = get_user_by_login("admin")
    if not admin:
        create_user(
            full_name="Admin",
            role="admin",
            login="admin",
            password_hash=hash_password("12345")
        )
        print("Standart admin yaratildi: login=admin password=12345")


if __name__ == "__main__":
    init_db()
    create_default_admin()
    executor.start_polling(dp, skip_updates=True)