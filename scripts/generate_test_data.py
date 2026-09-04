"""
Generate fully random synthetic test data for all 3 merchant accounts.

Creates accounts.csv and orders.csv in the data/ directory with
realistic-looking abuse rings mixed with legitimate accounts.
"""

import csv
import hashlib
import os
import random
import string
import uuid
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

MERCHANTS = [
    {"id": "d8e8be4b-8407-447a-a2f1-2db069e45dc2", "name": "Alpha Electronics"},
    {"id": "0e3c2cb1-1114-415c-a680-1204829213a3", "name": "Beta Fashion"},
    {"id": "1ed1d417-6ce7-4b1d-ba96-1a08097b591a", "name": "Gamma Groceries"},
]

# Config per merchant — randomized ring counts
RINGS_PER_MERCHANT = {m["id"]: random.randint(2, 5) for m in MERCHANTS}
LEGIT_ACCOUNTS_PER_MERCHANT = {m["id"]: random.randint(15, 35) for m in MERCHANTS}

PROMO_CODES = ["WELCOME10", "SAVE20", "FLASH50", "NEWUSER", "FREESHIP", "FLAT100", "MEGA30", "FIRST15"]
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com"]


def rand_hash():
    return hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]


def rand_email():
    name = ''.join(random.choices(string.ascii_lowercase, k=random.randint(5, 10)))
    num = random.randint(1, 999)
    domain = random.choice(DOMAINS)
    return f"{name}{num}@{domain}"


def rand_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"


def rand_time(base: datetime, spread_hours: int = 720):
    offset = random.randint(0, spread_hours * 3600)
    return base - timedelta(seconds=offset)


def generate():
    accounts = []
    orders = []
    now = datetime.utcnow()

    for merchant in MERCHANTS:
        mid = merchant["id"]
        num_rings = RINGS_PER_MERCHANT[mid]
        num_legit = LEGIT_ACCOUNTS_PER_MERCHANT[mid]

        # ── Abuse rings ──────────────────────────────────────────
        for ring_idx in range(num_rings):
            ring_size = random.randint(3, 6)

            # Shared signals (what makes them a "ring")
            num_shared = random.randint(1, 3)
            shared_device = rand_hash() if num_shared >= 1 else None
            shared_address = rand_hash() if num_shared >= 2 else None
            shared_card = rand_hash() if num_shared >= 3 else None

            # Tight signup window — within a few hours
            ring_base_time = rand_time(now, spread_hours=480)
            signup_window_minutes = random.randint(5, 120)

            for acct_idx in range(ring_size):
                acct_id = f"acct_{mid[:4]}_{ring_idx:02d}_{acct_idx:02d}"
                signup = ring_base_time + timedelta(minutes=random.randint(0, signup_window_minutes))

                accounts.append({
                    "account_id": acct_id,
                    "merchant_id": mid,
                    "email": rand_email(),
                    "phone": rand_phone(),
                    "device_hash": shared_device if shared_device else rand_hash(),
                    "address_hash": shared_address if shared_address else rand_hash(),
                    "card_hash": shared_card if shared_card else rand_hash(),
                    "signup_time": signup.isoformat(),
                })

                # Each ring account places 1-4 orders, often with promos & refunds
                num_orders = random.randint(1, 4)
                for o in range(num_orders):
                    orders.append({
                        "order_id": f"ord_{uuid.uuid4().hex[:10]}",
                        "account_id": acct_id,
                        "merchant_id": mid,
                        "amount": round(random.uniform(50, 5000), 2),
                        "promo_code_used": random.choice(PROMO_CODES) if random.random() > 0.3 else "",
                        "refund_requested": random.random() > 0.5,
                        "order_time": (signup + timedelta(minutes=random.randint(1, 2880))).isoformat(),
                    })

        # ── Legitimate accounts ──────────────────────────────────
        for _ in range(num_legit):
            acct_id = f"acct_{uuid.uuid4().hex[:10]}"
            signup = rand_time(now, spread_hours=720)

            accounts.append({
                "account_id": acct_id,
                "merchant_id": mid,
                "email": rand_email(),
                "phone": rand_phone(),
                "device_hash": rand_hash(),
                "address_hash": rand_hash(),
                "card_hash": rand_hash(),
                "signup_time": signup.isoformat(),
            })

            # Legit users: 1-3 orders, rarely use promos, rarely refund
            num_orders = random.randint(1, 3)
            for o in range(num_orders):
                orders.append({
                    "order_id": f"ord_{uuid.uuid4().hex[:10]}",
                    "account_id": acct_id,
                    "merchant_id": mid,
                    "amount": round(random.uniform(100, 8000), 2),
                    "promo_code_used": random.choice(PROMO_CODES) if random.random() > 0.85 else "",
                    "refund_requested": random.random() > 0.9,
                    "order_time": (signup + timedelta(minutes=random.randint(60, 43200))).isoformat(),
                })

    # ── Write CSVs ────────────────────────────────────────────
    os.makedirs(DATA_DIR, exist_ok=True)

    acct_path = os.path.join(DATA_DIR, "accounts.csv")
    with open(acct_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["account_id", "merchant_id", "email", "phone",
                                           "device_hash", "address_hash", "card_hash", "signup_time"])
        w.writeheader()
        w.writerows(accounts)

    orders_path = os.path.join(DATA_DIR, "orders.csv")
    with open(orders_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["order_id", "account_id", "merchant_id", "amount",
                                           "promo_code_used", "refund_requested", "order_time"])
        w.writeheader()
        w.writerows(orders)

    print(f"Generated {len(accounts)} accounts across {len(MERCHANTS)} merchants")
    for m in MERCHANTS:
        mid = m["id"]
        m_accts = [a for a in accounts if a["merchant_id"] == mid]
        m_orders = [o for o in orders if o["merchant_id"] == mid]
        rings = RINGS_PER_MERCHANT[mid]
        legit = LEGIT_ACCOUNTS_PER_MERCHANT[mid]
        print(f"  {m['name']}: {len(m_accts)} accounts ({rings} rings + {legit} legit), {len(m_orders)} orders")
    print(f"Generated {len(orders)} orders total")
    print(f"Files: {acct_path}, {orders_path}")


if __name__ == "__main__":
    generate()
