import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    bot_token: str
    admin_id: int
    database_path: str = "bot.db"
    
    class Config:
        env_file = ".env"


# Явно загружаем .env файл
from dotenv import load_dotenv
load_dotenv()

settings = Settings()

# Отладка - выводим загруженные значения
print(f"DEBUG: BOT_TOKEN={settings.bot_token[:10]}...")
print(f"DEBUG: ADMIN_ID={settings.admin_id}")
print(f"DEBUG: DATABASE_PATH={settings.database_path}")
