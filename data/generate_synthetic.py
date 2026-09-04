"""
Synthetic data generator for Abuse-Ring Sentinel.

Produces:
  - accounts.csv   (~2000 normal + fraud ring + innocent cluster accounts)
  - orders.csv     (orders for all accounts)
  - ground_truth.json  (planted rings + innocent clusters for eval)

Each account/order is assigned to one of the seeded demo merchants.

Usage:  python data/generate_synthetic.py
"""

import sys
import os
import json
import random
import hashlib
from datetime import datetime, timedelta

import pandas as pd

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.supabase_client import get_service_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SEED = 42
NUM_NORMAL_ACCOUNTS = 2000
NUM_FRAUD_RINGS = 20
FRAUD_RING_SIZE_RANGE = (3, 8)      # accounts per ring
NUM_INNOCENT_CLUSTERS = 5
INNOCENT_CLUSTER_SIZE_RANGE = (3, 5) # must be >=3 so detector can pick them up

# Time range
BASE_TIME = datetime(2024, 1, 1)
NORMAL_SPREAD_DAYS = 365             # normal accounts spread over a year
FRAUD_SIGNUP_WINDOW_HOURS = 72       # fraud ring accounts created within 72 h
INNOCENT_SIGNUP_SPREAD_DAYS = 90     # families sign up over weeks/months

random.seed(SEED)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash(value: str) -> str:
    """Deterministic 16-char hex hash for signal values."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _email(prefix: str) -> str:
    domains = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com",
               "hotmail.com", "rediffmail.com"]
    return f"{prefix}_{random.randint(1000, 9999)}@{random.choice(domains)}"


def _phone() -> str:
    return f"+91{random.randint(7000000000, 9999999999)}"


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def generate_normal_accounts(merchant_ids: list[str]) -> list[dict]:
    """~2000 independent accounts, every signal unique."""
    accounts = []
    for i in range(NUM_NORMAL_ACCOUNTS):
        aid = f"acct_norm_{i:04d}"
        signup = BASE_TIME + timedelta(days=random.uniform(0, NORMAL_SPREAD_DAYS))
        accounts.append({
            "account_id": aid,
            "merchant_id": random.choice(merchant_ids),
            "email": _email(f"user{i}"),
            "phone": _phone(),
            "device_hash": _hash(f"dev_uniq_{aid}"),
            "address_hash": _hash(f"addr_uniq_{aid}"),
            "card_hash": _hash(f"card_uniq_{aid}"),
            "signup_time": signup.isoformat(),
        })
    return accounts


def generate_fraud_rings(merchant_ids: list[str]) -> tuple[list[dict], list[dict]]:
    """
    ~20 fraud rings, each sharing 1-3 signals.
    Tight signup window, heavy promo/refund usage (handled in order generation).
    """
    accounts = []
    ground_truth = []
    signal_cols = ["device_hash", "address_hash", "card_hash"]

    for ring_idx in range(NUM_FRAUD_RINGS):
        ring_id = f"ring_{ring_idx:03d}"
        ring_size = random.randint(*FRAUD_RING_SIZE_RANGE)

        # Pick which signals this ring shares (1-3)
        num_shared = random.randint(1, 3)
        shared_signals = random.sample(signal_cols, num_shared)
        shared_values = {sig: _hash(f"shared_{ring_id}_{sig}") for sig in shared_signals}

        # Most rings target one merchant
        ring_merchant = random.choice(merchant_ids)

        # Tight signup window
        ring_base = BASE_TIME + timedelta(days=random.uniform(0, NORMAL_SPREAD_DAYS))

        ring_account_ids = []
        for j in range(ring_size):
            aid = f"acct_ring{ring_idx:03d}_{j:02d}"
            signup = ring_base + timedelta(hours=random.uniform(0, FRAUD_SIGNUP_WINDOW_HOURS))

            acct = {
                "account_id": aid,
                "merchant_id": ring_merchant,
                "email": _email(f"r{ring_idx}u{j}"),
                "phone": _phone(),
                "device_hash": _hash(f"dev_uniq_{aid}"),
                "address_hash": _hash(f"addr_uniq_{aid}"),
                "card_hash": _hash(f"card_uniq_{aid}"),
                "signup_time": signup.isoformat(),
            }
            # Override the shared signals with shared values
            for sig in shared_signals:
                acct[sig] = shared_values[sig]

            accounts.append(acct)
            ring_account_ids.append(aid)

        ground_truth.append({
            "cluster_id": ring_id,
            "account_ids": ring_account_ids,
            "is_fraud_ring": True,
            "shared_signals": shared_signals,
        })

    return accounts, ground_truth


def generate_innocent_clusters(merchant_ids: list[str]) -> tuple[list[dict], list[dict]]:
    """
    Innocent look-alike clusters: families/roommates sharing an address
    (and sometimes a card). Size >= 3 so the detector can actually pick
    them up — this is required for an honest false-positive story.
    """
    accounts = []
    ground_truth = []

    for cidx in range(NUM_INNOCENT_CLUSTERS):
        cluster_id = f"innocent_{cidx:03d}"
        cluster_size = random.randint(*INNOCENT_CLUSTER_SIZE_RANGE)

        # All share address; ~60% also share a card (joint family card)
        shared_addr = _hash(f"family_addr_{cluster_id}")
        share_card = random.random() < 0.6
        shared_card = _hash(f"family_card_{cluster_id}") if share_card else None

        merchant = random.choice(merchant_ids)
        base = BASE_TIME + timedelta(days=random.uniform(0, NORMAL_SPREAD_DAYS))

        ids = []
        for j in range(cluster_size):
            aid = f"acct_inno{cidx:03d}_{j:02d}"
            signup = base + timedelta(days=random.uniform(0, INNOCENT_SIGNUP_SPREAD_DAYS))

            acct = {
                "account_id": aid,
                "merchant_id": merchant,
                "email": _email(f"fam{cidx}m{j}"),
                "phone": _phone(),
                "device_hash": _hash(f"dev_uniq_{aid}"),  # each family member has own device
                "address_hash": shared_addr,
                "card_hash": shared_card if shared_card else _hash(f"card_uniq_{aid}"),
                "signup_time": signup.isoformat(),
            }
            accounts.append(acct)
            ids.append(aid)

        shared_sigs = ["address_hash"]
        if share_card:
            shared_sigs.append("card_hash")

        ground_truth.append({
            "cluster_id": cluster_id,
            "account_ids": ids,
            "is_fraud_ring": False,
            "shared_signals": shared_sigs,
        })

    return accounts, ground_truth


def generate_orders(all_accounts: list[dict], fraud_ids: set[str]) -> list[dict]:
    """
    Generate orders per account.
    Fraud accounts: more orders, heavy promo usage (~80%), high refund rate (~40%).
    Normal/innocent: fewer orders, light promo usage (~15%), low refund rate (~5%).
    """
    orders = []
    promos = ["WELCOME50", "FIRSTORDER", "BOGO2024", "NEWUSER", "FLAT200",
              "SAVE30", "FREESHIP"]

    for acct in all_accounts:
        aid = acct["account_id"]
        is_fraud = aid in fraud_ids
        num_orders = random.randint(3, 8) if is_fraud else random.randint(1, 5)
        signup = datetime.fromisoformat(acct["signup_time"])

        for k in range(num_orders):
            order_time = signup + timedelta(
                days=random.uniform(0, 7 if is_fraud else 60)
            )

            if is_fraud:
                promo = random.choice(promos) if random.random() < 0.80 else None
                refund = random.random() < 0.40
                amount = round(random.uniform(100, 2000), 2)
            else:
                promo = random.choice(promos) if random.random() < 0.15 else None
                refund = random.random() < 0.05
                amount = round(random.uniform(200, 15000), 2)

            orders.append({
                "order_id": f"ord_{aid}_{k:02d}",
                "account_id": aid,
                "merchant_id": acct["merchant_id"],
                "amount": amount,
                "promo_code_used": promo if promo else "",
                "refund_requested": refund,
                "order_time": order_time.isoformat(),
            })

    return orders


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Abuse-Ring Sentinel — Synthetic Data Generator")
    print("=" * 60)

    # Fetch real merchant IDs from Supabase
    sb = get_service_client()
    merchants_resp = sb.table("merchants").select("id, name").execute()
    merchant_ids = [m["id"] for m in merchants_resp.data]
    print(f"\nMerchants loaded: {len(merchant_ids)}")
    for m in merchants_resp.data:
        print(f"  {m['name']}  ({m['id'][:8]}…)")

    # --- Generate accounts ---
    print(f"\nGenerating {NUM_NORMAL_ACCOUNTS} normal accounts …")
    normal_accts = generate_normal_accounts(merchant_ids)

    print(f"Generating {NUM_FRAUD_RINGS} fraud rings …")
    fraud_accts, fraud_gt = generate_fraud_rings(merchant_ids)
    fraud_ids = {a["account_id"] for a in fraud_accts}

    print(f"Generating {NUM_INNOCENT_CLUSTERS} innocent look-alike clusters …")
    innocent_accts, innocent_gt = generate_innocent_clusters(merchant_ids)

    all_accounts = normal_accts + fraud_accts + innocent_accts
    random.shuffle(all_accounts)

    # --- Generate orders ---
    print("Generating orders …")
    all_orders = generate_orders(all_accounts, fraud_ids)

    # --- Ground truth ---
    ground_truth = fraud_gt + innocent_gt

    # --- Save to disk ---
    data_dir = os.path.dirname(os.path.abspath(__file__))

    accts_df = pd.DataFrame(all_accounts)
    accts_path = os.path.join(data_dir, "accounts.csv")
    accts_df.to_csv(accts_path, index=False)

    orders_df = pd.DataFrame(all_orders)
    orders_path = os.path.join(data_dir, "orders.csv")
    orders_df.to_csv(orders_path, index=False)

    gt_path = os.path.join(data_dir, "ground_truth.json")
    with open(gt_path, "w") as f:
        json.dump(ground_truth, f, indent=2)

    # --- Summary ---
    total_fraud_accts = sum(len(g["account_ids"]) for g in fraud_gt)
    total_inno_accts = sum(len(g["account_ids"]) for g in innocent_gt)

    print(f"\n{'-' * 50}")
    print(f"  GENERATION SUMMARY")
    print(f"{'-' * 50}")
    print(f"  Normal accounts:      {len(normal_accts):>6}")
    print(f"  Fraud ring accounts:  {total_fraud_accts:>6}  ({len(fraud_gt)} rings)")
    print(f"  Innocent cluster:     {total_inno_accts:>6}  ({len(innocent_gt)} clusters)")
    print(f"  Total accounts:       {len(all_accounts):>6}")
    print(f"  Total orders:         {len(all_orders):>6}")
    print(f"{'-' * 50}")
    print(f"  Saved -> {accts_path}")
    print(f"  Saved -> {orders_path}")
    print(f"  Saved -> {gt_path}")

    # Detail tables
    print(f"\n  PLANTED FRAUD RINGS")
    print(f"  {'ID':<12} {'Size':>4}  Shared Signals")
    print(f"  {'-'*12} {'-'*4}  {'-'*30}")
    for g in fraud_gt:
        print(f"  {g['cluster_id']:<12} {len(g['account_ids']):>4}  {', '.join(g['shared_signals'])}")

    print(f"\n  INNOCENT LOOK-ALIKE CLUSTERS")
    print(f"  {'ID':<16} {'Size':>4}  Shared Signals")
    print(f"  {'-'*16} {'-'*4}  {'-'*30}")
    for g in innocent_gt:
        print(f"  {g['cluster_id']:<16} {len(g['account_ids']):>4}  {', '.join(g['shared_signals'])}")


if __name__ == "__main__":
    main()
