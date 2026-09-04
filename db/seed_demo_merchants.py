"""
Seed 2-3 demo merchant accounts via Supabase Auth (service_role key).
Run once after schema.sql has been applied.

Usage:  python db/seed_demo_merchants.py
"""

import sys
import os

# Allow running from project root: `python db/seed_demo_merchants.py`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import get_service_client


DEMO_MERCHANTS = [
    {
        "email": "merchant_alpha@demo.sentinel",
        "password": "DemoPass123!",
        "name": "Alpha Electronics",
    },
    {
        "email": "merchant_beta@demo.sentinel",
        "password": "DemoPass456!",
        "name": "Beta Fashion",
    },
    {
        "email": "merchant_gamma@demo.sentinel",
        "password": "DemoPass789!",
        "name": "Gamma Groceries",
    },
]


def seed_merchants():
    sb = get_service_client()
    created = []

    for m in DEMO_MERCHANTS:
        print(f"Creating auth user: {m['email']} ... ", end="")

        # Create user in Supabase Auth
        res = sb.auth.admin.create_user(
            {
                "email": m["email"],
                "password": m["password"],
                "email_confirm": True,  # auto-confirm so we can log in immediately
            }
        )

        user_id = res.user.id
        print(f"OK  (id={user_id})")

        # Insert matching row in our merchants table
        sb.table("merchants").insert(
            {"id": user_id, "name": m["name"], "email": m["email"]}
        ).execute()

        created.append({"merchant_id": user_id, "email": m["email"], "name": m["name"]})

    print("\n--- Seeded merchants ---")
    for c in created:
        print(f"  {c['name']:20s}  {c['email']:35s}  id={c['merchant_id']}")

    return created


if __name__ == "__main__":
    seed_merchants()
