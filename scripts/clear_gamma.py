"""
Removes all synthetic data for Gamma Groceries from accounts.csv and orders.csv.
"""
import os
import pandas as pd

GAMMA_ID = "1ed1d417-6ce7-4b1d-ba96-1a08097b591a"

def clear_gamma_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    accounts_file = os.path.join(base_dir, "data", "accounts.csv")
    orders_file = os.path.join(base_dir, "data", "orders.csv")

    # Clear accounts
    if os.path.exists(accounts_file):
        df_accounts = pd.read_csv(accounts_file)
        initial_len = len(df_accounts)
        df_accounts = df_accounts[df_accounts["merchant_id"] != GAMMA_ID]
        df_accounts.to_csv(accounts_file, index=False)
        print(f"Removed {initial_len - len(df_accounts)} accounts for Gamma Groceries.")

    # Clear orders
    if os.path.exists(orders_file):
        df_orders = pd.read_csv(orders_file)
        initial_len = len(df_orders)
        df_orders = df_orders[df_orders["merchant_id"] != GAMMA_ID]
        df_orders.to_csv(orders_file, index=False)
        print(f"Removed {initial_len - len(df_orders)} orders for Gamma Groceries.")

if __name__ == "__main__":
    clear_gamma_data()
