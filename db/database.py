"""
Local SQLite database for Sentinel.

Provides:
  - init_db()            → create tables if they don't exist
  - get_db()             → returns a sqlite3 connection
  - get_merchant_by_email(email)
  - get_merchant_by_id(mid)
  - update_merchant(mid, data)
"""

import os
import sqlite3

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "sentinel.db")


def get_db() -> sqlite3.Connection:
    """Return a connection with row_factory set for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS merchants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar_url TEXT
        );
    """)
    conn.commit()
    conn.close()


def get_merchant_by_email(email: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM merchants WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_merchant_by_id(merchant_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM merchants WHERE id = ?", (merchant_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_merchant(merchant_id: str, data: dict):
    """Update merchant fields. `data` is a dict of column: value pairs."""
    if not data:
        return
    conn = get_db()
    set_clause = ", ".join(f"{k} = ?" for k in data.keys())
    values = list(data.values()) + [merchant_id]
    conn.execute(f"UPDATE merchants SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def merchant_count() -> int:
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM merchants").fetchone()[0]
    conn.close()
    return count
