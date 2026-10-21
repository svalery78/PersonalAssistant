import sqlite3
from contextlib import contextmanager

from config import DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vk_user_id INTEGER NOT NULL,
                user_text TEXT NOT NULL,
                assistant_text TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS conversation_turns_user
            ON conversation_turns (vk_user_id, id)
        """)


def get_history(vk_user_id: int, max_turns: int) -> list[dict[str, str]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT user_text, assistant_text FROM conversation_turns "
            "WHERE vk_user_id = ? ORDER BY id DESC LIMIT ?",
            (vk_user_id, max_turns),
        ).fetchall()
    return [
        {"role": role, "content": text}
        for user_text, assistant_text in reversed(rows)
        for role, text in (("user", user_text), ("assistant", assistant_text))
    ]


def save_turn(vk_user_id: int, user_text: str, answer: str, max_turns: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO conversation_turns (vk_user_id, user_text, assistant_text) "
            "VALUES (?, ?, ?)", (vk_user_id, user_text, answer),
        )
        conn.execute(
            "DELETE FROM conversation_turns WHERE vk_user_id = ? AND id NOT IN "
            "(SELECT id FROM conversation_turns WHERE vk_user_id = ? "
            "ORDER BY id DESC LIMIT ?)", (vk_user_id, vk_user_id, max_turns),
        )


def delete_history(vk_user_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM conversation_turns WHERE vk_user_id = ?", (vk_user_id,))
