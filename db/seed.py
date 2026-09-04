"""
Seed the local SQLite database with 3 demo merchant accounts.

Run automatically on startup if the merchants table is empty.
Can also be run standalone: python -m db.seed
"""

import uuid
import bcrypt
from db.database import init_db, get_db, merchant_count

DEMO_MERCHANTS = [
    {
        "id": "d8e8be4b-8407-447a-a2f1-2db069e45dc2",
        "name": "Alpha Electronics",
        "email": "merchant_alpha@demo.sentinel",
        "password": "password123",
    },
    {
        "id": "0e3c2cb1-1114-415c-a680-1204829213a3",
        "name": "Beta Fashion",
        "email": "merchant_beta@demo.sentinel",
        "password": "password123",
    },
    {
        "id": "1ed1d417-6ce7-4b1d-ba96-1a08097b591a",
        "name": "Gamma Groceries",
        "email": "merchant_gamma@demo.sentinel",
        "password": "password123",
    },
]


def seed():
    """Insert demo merchants if the table is empty."""
    init_db()

    if merchant_count() > 0:
        print("Database already seeded — skipping.")
        return

    conn = get_db()
    for m in DEMO_MERCHANTS:
        pw_hash = bcrypt.hashpw(m["password"].encode(), bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO merchants (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (m["id"], m["name"], m["email"], pw_hash),
        )
    conn.commit()
    conn.close()
    print(f"Seeded {len(DEMO_MERCHANTS)} demo merchant accounts.")


if __name__ == "__main__":
    seed()
