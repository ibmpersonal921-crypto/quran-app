"""
database/db.py
---------------
Zero-setup local persistence using SQLite (no server, no cost — the whole
point of "free"). Stores: daily goals, completion log (for streaks), chat
history, and recitation-coach session results.
"""

import sqlite3
import datetime as dt
from contextlib import contextmanager

from config import DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                description TEXT NOT NULL,
                points INTEGER NOT NULL DEFAULT 5,
                is_done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS completion_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                points INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recitation_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                surah INTEGER,
                ayah INTEGER,
                accuracy REAL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------
def add_goal(goal_type: str, description: str, points: int, date: str = None) -> None:
    date = date or dt.date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO goals (date, goal_type, description, points, is_done, created_at) "
            "VALUES (?, ?, ?, ?, 0, ?)",
            (date, goal_type, description, points, dt.datetime.now().isoformat()),
        )


def get_goals_for_date(date: str = None) -> list:
    date = date or dt.date.today().isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM goals WHERE date = ? ORDER BY id", (date,)
        ).fetchall()
        return [dict(r) for r in rows]


def toggle_goal(goal_id: int, is_done: bool) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE goals SET is_done = ? WHERE id = ?", (int(is_done), goal_id))
        goal = conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
        if goal and is_done:
            conn.execute(
                "INSERT INTO completion_log (date, points) VALUES (?, ?)",
                (goal["date"], goal["points"]),
            )
        elif goal and not is_done:
            conn.execute(
                "DELETE FROM completion_log WHERE date = ? AND points = ? "
                "AND id = (SELECT id FROM completion_log WHERE date = ? AND points = ? LIMIT 1)",
                (goal["date"], goal["points"], goal["date"], goal["points"]),
            )


def delete_goal(goal_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))


def get_all_completion_dates() -> list:
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT date FROM completion_log").fetchall()
        return [r["date"] for r in rows]


def get_total_points() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COALESCE(SUM(points), 0) AS total FROM completion_log").fetchone()
        return row["total"]


def get_points_today() -> int:
    today = dt.date.today().isoformat()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(points), 0) AS total FROM completion_log WHERE date = ?", (today,)
        ).fetchone()
        return row["total"]


# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------
def log_chat(role: str, content: str, sources: str = "") -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_history (role, content, sources, created_at) VALUES (?, ?, ?, ?)",
            (role, content, sources, dt.datetime.now().isoformat()),
        )


def get_chat_history(limit: int = 100) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows][::-1]


def clear_chat_history() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM chat_history")


# ---------------------------------------------------------------------------
# Recitation sessions
# ---------------------------------------------------------------------------
def log_recitation_session(surah: int, ayah: int, accuracy: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO recitation_sessions (surah, ayah, accuracy, created_at) VALUES (?, ?, ?, ?)",
            (surah, ayah, accuracy, dt.datetime.now().isoformat()),
        )


def get_recitation_history(limit: int = 20) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM recitation_sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Settings (key/value)
# ---------------------------------------------------------------------------
def set_setting(key: str, value: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_setting(key: str, default: str = None) -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default
