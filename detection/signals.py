"""
Signal extraction layer.

Loads accounts + orders from CSV and prepares signal columns
for the clustering engine. No LLM involvement.
"""

import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

SIGNAL_COLUMNS = ["device_hash", "address_hash", "card_hash"]


def load_accounts(path: str | None = None) -> pd.DataFrame:
    """Load accounts.csv, parse signup_time as datetime."""
    p = path or os.path.join(DATA_DIR, "accounts.csv")
    df = pd.read_csv(p)
    df["signup_time"] = pd.to_datetime(df["signup_time"], format='mixed')
    return df


def load_orders(path: str | None = None) -> pd.DataFrame:
    """Load orders.csv, parse order_time as datetime."""
    p = path or os.path.join(DATA_DIR, "orders.csv")
    df = pd.read_csv(p)
    df["order_time"] = pd.to_datetime(df["order_time"], format='mixed')
    # Normalize promo_code_used: empty string / NaN -> None-ish for boolean checks
    df["promo_code_used"] = df["promo_code_used"].fillna("")
    return df


def extract_account_signals(accounts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a view of accounts with only the columns needed for clustering:
    account_id, merchant_id, signup_time, + each signal hash column.
    """
    required = ["account_id", "merchant_id", "signup_time"] + SIGNAL_COLUMNS
    for col in required:
        if col not in accounts_df.columns:
            raise ValueError(f"Missing required column: {col}")
    return accounts_df[required].copy()


if __name__ == "__main__":
    accts = load_accounts()
    orders = load_orders()
    signals = extract_account_signals(accts)
    print(f"Loaded {len(accts)} accounts, {len(orders)} orders")
    print(f"Signal columns: {SIGNAL_COLUMNS}")
    print(f"\nSample signals (first 5):")
    print(signals.head().to_string(index=False))
