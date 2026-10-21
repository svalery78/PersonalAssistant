import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
SYSTEM_PROMPT_FILE = PROJECT_DIR / os.getenv("SYSTEM_PROMPT_FILE", "system_prompt.txt")
HISTORY_MAX_TURNS = int(os.getenv("HISTORY_MAX_TURNS", "20"))
DB_PATH = PROJECT_DIR / os.getenv("DB_PATH", "bot.db")

VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN")
VK_SECRET = os.getenv("VK_SECRET")
VK_API_VERSION = os.getenv("VK_API_VERSION", "5.199")

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8000"))


def validate_config():
    required = {
        "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
        "OPENROUTER_MODEL": OPENROUTER_MODEL,
        "VK_GROUP_TOKEN": VK_GROUP_TOKEN,
        "VK_CONFIRMATION_TOKEN": VK_CONFIRMATION_TOKEN,
        "VK_SECRET": VK_SECRET,
    }
    missing = [name for name, value in required.items() if not value or not value.strip()]
    if missing:
        raise RuntimeError(f"Не заполнены переменные окружения: {', '.join(missing)}")
    if HISTORY_MAX_TURNS < 1:
        raise RuntimeError("HISTORY_MAX_TURNS должен быть больше нуля")
    if not SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip():
        raise RuntimeError("Файл системного промпта пуст")
