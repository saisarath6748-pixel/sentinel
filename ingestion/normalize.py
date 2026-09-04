"""
Normalization layer.

Maps Razorpay payment fields into the same schema used by the synthetic
data (accounts.csv / orders.csv) so the detection engine sees one unified
format regardless of data source.

Per the brief (section 8): Razorpay's payment API provides email, contact,
card_id, and timing — but NOT device fingerprint or shipping address.
In production, Razorpay's own checkout SDK captures device/browser signals
at payment time, and shipping address is passed during order creation.
For this demo, we simulate those platform-level signals with deterministic
hashes derived from available fields.

Usage (standalone test):
    python -m ingestion.normalize
"""

import hashlib
import os
import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _hash(value: str) -> str:
    """Deterministic 16-char hex hash."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def normalize_razorpay_payments(
    payments: list[dict],
    merchant_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert Razorpay payment records into the sentinel's unified schema.

    Args:
        payments: list from razorpay_client.fetch_recent_payments()
        merchant_id: UUID of the merchant these payments belong to

    Returns:
        (accounts_df, orders_df) in the same schema as synthetic data

    Note on simulated signals:
        - device_hash: derived from contact (in production, Razorpay's checkout
          SDK would capture the actual device/browser fingerprint)
        - address_hash: derived from email domain (in production, shipping
          address would come from order metadata passed to Razorpay)
        - card_hash: uses Razorpay's tokenized card_id directly
    """
    seen_accounts = {}
    orders = []

    for p in payments:
        email = p.get("email", "")
        contact = p.get("contact", "")
        card_id = p.get("card_id", "")

        # Derive a stable account_id from email (one account per email)
        if not email:
            continue
        acct_id = f"rzp_{_hash(email)[:10]}"

        # Build account record (deduplicated by email)
        if acct_id not in seen_accounts:
            seen_accounts[acct_id] = {
                "account_id": acct_id,
                "merchant_id": merchant_id,
                "email": email,
                "phone": contact,
                # Simulated platform signals (see docstring)
                "device_hash": _hash(f"device_{contact}") if contact else _hash(f"device_{email}"),
                "address_hash": _hash(f"address_{email.split('@')[0]}"),
                "card_hash": _hash(f"card_{card_id}") if card_id else _hash(f"card_{email}"),
                "signup_time": p.get("created_at", datetime.now().isoformat()),
            }

        # Build order record
        orders.append({
            "order_id": f"rzp_ord_{p['payment_id']}",
            "account_id": acct_id,
            "merchant_id": merchant_id,
            "amount": p.get("amount", 0),
            "promo_code_used": "",
            "refund_requested": False,
            "order_time": p.get("created_at", datetime.now().isoformat()),
        })

    accounts_df = pd.DataFrame(list(seen_accounts.values()))
    orders_df = pd.DataFrame(orders)

    return accounts_df, orders_df


def merge_with_synthetic(
    rzp_accounts: pd.DataFrame,
    rzp_orders: pd.DataFrame,
    synthetic_accounts_path: str | None = None,
    synthetic_orders_path: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Merge Razorpay-normalized data with existing synthetic CSVs.
    Returns combined DataFrames.
    """
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )
    accts_path = synthetic_accounts_path or os.path.join(data_dir, "accounts.csv")
    ords_path = synthetic_orders_path or os.path.join(data_dir, "orders.csv")

    syn_accts = pd.read_csv(accts_path)
    syn_ords = pd.read_csv(ords_path)

    if not rzp_accounts.empty:
        combined_accts = pd.concat([syn_accts, rzp_accounts], ignore_index=True)
    else:
        combined_accts = syn_accts

    if not rzp_orders.empty:
        combined_ords = pd.concat([syn_ords, rzp_orders], ignore_index=True)
    else:
        combined_ords = syn_ords

    return combined_accts, combined_ords


if __name__ == "__main__":
    from ingestion.razorpay_client import fetch_recent_payments
    from db.supabase_client import get_service_client

    print("=" * 60)
    print("  Razorpay -> Sentinel Normalization")
    print("=" * 60)

    # Fetch payments
    try:
        payments = fetch_recent_payments()
    except Exception as e:
        print(f"\n  ERROR fetching payments: {e}")
        sys.exit(1)

    print(f"\n  Fetched {len(payments)} Razorpay payments")

    if not payments:
        print("  No payments to normalize. Create test payments first.")
        sys.exit(0)

    # Use first demo merchant
    sb = get_service_client()
    merchants = sb.table("merchants").select("id, name").execute()
    merchant_id = merchants.data[0]["id"]
    merchant_name = merchants.data[0]["name"]
    print(f"  Assigning to merchant: {merchant_name} ({merchant_id[:8]}...)")

    # Normalize
    rzp_accts, rzp_ords = normalize_razorpay_payments(payments, merchant_id)
    print(f"\n  Normalized:")
    print(f"    Accounts: {len(rzp_accts)}")
    print(f"    Orders:   {len(rzp_ords)}")

    # Merge with synthetic
    combined_accts, combined_ords = merge_with_synthetic(rzp_accts, rzp_ords)
    print(f"\n  After merging with synthetic data:")
    print(f"    Total accounts: {len(combined_accts)}")
    print(f"    Total orders:   {len(combined_ords)}")

    # Show Razorpay accounts
    if not rzp_accts.empty:
        print(f"\n  Razorpay-derived accounts:")
        print(f"  {'ID':<18} {'Email':<30} {'Device':<18} {'Card':<18}")
        print(f"  {'-'*18} {'-'*30} {'-'*18} {'-'*18}")
        for _, row in rzp_accts.iterrows():
            print(
                f"  {row['account_id']:<18} "
                f"{row['email']:<30} "
                f"{row['device_hash']:<18} "
                f"{row['card_hash']:<18}"
            )
