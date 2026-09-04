"""
Razorpay test-mode payment ingestion.

Pulls recent payments from Razorpay's API using test-mode credentials.
This is the only file that touches the Razorpay SDK.

Usage (standalone test):
    python -m ingestion.razorpay_client
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_client():
    """Lazy-init Razorpay client."""
    import razorpay

    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise RuntimeError(
            "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set in .env"
        )
    if key_id.startswith("rzp_test_xxx"):
        raise RuntimeError(
            "RAZORPAY_KEY_ID is still the placeholder value. "
            "Replace it with your real test-mode key."
        )

    return razorpay.Client(auth=(key_id, key_secret))


def fetch_recent_payments(count: int = 50) -> list[dict]:
    """
    Fetch recent payments from Razorpay test mode.

    Returns list of dicts with fields:
        payment_id, amount, email, contact, method, card_id, created_at
    """
    client = _get_client()
    response = client.payment.all({"count": count})
    items = response.get("items", [])

    payments = []
    for p in items:
        card_obj = p.get("card") or {}
        card_info = None
        if card_obj and (card_obj.get("last4") or card_obj.get("token_iin") or card_obj.get("network")):
            card_info = {
                "id": card_obj.get("id", ""),
                "last4": card_obj.get("last4", ""),
                "network": card_obj.get("network", ""),
                "type": card_obj.get("type", ""),
                "issuer": card_obj.get("issuer", ""),
                "token_iin": card_obj.get("token_iin", ""),
                "name": card_obj.get("name", ""),
            }

        payments.append({
            "payment_id": p.get("id", ""),
            "amount": p.get("amount", 0) / 100,  # paise -> rupees
            "email": p.get("email", ""),
            "contact": p.get("contact", ""),
            "method": p.get("method", ""),
            "card_id": p.get("card_id") or "",      # tokenized, never raw
            "card": card_info,
            "vpa": p.get("vpa") or "",
            "notes": p.get("notes") or {},
            "description": p.get("description") or "",
            "created_at": datetime.fromtimestamp(
                p.get("created_at", 0)
            ).isoformat() if p.get("created_at") else "",
            "status": p.get("status", ""),
            "order_id": p.get("order_id") or "",
        })

    return payments


if __name__ == "__main__":
    print("=" * 60)
    print("  Razorpay Test-Mode Payment Fetch")
    print("=" * 60)

    try:
        payments = fetch_recent_payments()
    except Exception as e:
        print(f"\n  ERROR: {e}")
        sys.exit(1)

    print(f"\n  Fetched {len(payments)} payments from Razorpay test mode\n")

    if not payments:
        print("  No payments found. To create test payments:")
        print("  1. Go to https://dashboard.razorpay.com (Test Mode)")
        print("  2. Use Smart Collect or Payment Links to create a test payment")
        print("  3. Use test card: 4111 1111 1111 1111, any future expiry, any CVV")
        print("  4. Re-run this script")
    else:
        print(f"  {'ID':<22} {'Amount':>8}  {'Method':<8}  {'Email':<30}  Status")
        print(f"  {'-'*22} {'-'*8}  {'-'*8}  {'-'*30}  {'-'*10}")
        for p in payments:
            print(
                f"  {p['payment_id']:<22} "
                f"{p['amount']:>8.2f}  "
                f"{p['method']:<8}  "
                f"{p['email']:<30}  "
                f"{p['status']}"
            )
