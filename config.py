import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylda topilmadi")