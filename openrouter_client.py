import requests

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    SYSTEM_PROMPT_FILE,
    HISTORY_MAX_TURNS,
)
from db import get_history, save_turn

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
EMPTY_ANSWER = "Не получилось сформировать ответ. Попробуй переформулировать вопрос."


def ask_openrouter(vk_user_id: int, user_text: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_FILE.read_text(encoding="utf-8").strip()},
        *get_history(vk_user_id, HISTORY_MAX_TURNS),
        {"role": "user", "content": user_text},
    ]
    response = requests.post(
        OPENROUTER_API_URL,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={"model": OPENROUTER_MODEL, "messages": messages},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError("OpenRouter вернул ошибку API")
    choices = data.get("choices") or []
    if not choices:
        return EMPTY_ANSWER
    answer = (choices[0].get("message") or {}).get("content")
    if not isinstance(answer, str) or not answer.strip():
        return EMPTY_ANSWER
    answer = answer.strip()
    # Записываем пару сообщений только после успешного текстового ответа.
    save_turn(vk_user_id, user_text, answer, HISTORY_MAX_TURNS)
    return answer
