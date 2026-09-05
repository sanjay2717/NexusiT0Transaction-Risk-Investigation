"""
Generate synthetic customer transaction data for the Transaction Risk
Investigation Assistant.

Customer-to-rule mapping (internal, not exposed to the frontend):
  C001 / Aarav Shah       — clean (no rules fire)
  C002 / Priya Menon      — Rule 1 only  (unusually large transfer)
  C003 / Rohan Iyer       — Rule 2 only  (burst to newly added payee)
  C004 / Sneha Kapoor     — Rule 3 only  (odd-hours activity)
  C005 / Vikram Nair      — Rules 1 + 3  (multi-rule, the hard demo case)
"""
import json
import random
from datetime import datetime, timedelta
import os

random.seed(42)

PAYEES = [
    "Grocery Store", "Electric Board", "Amazon", "Local Restaurant",
    "Netflix", "Gas Station",
]
CHANNELS = ["UPI", "Credit Card", "Debit Card", "Net Banking"]
DESCRIPTIONS = ["Payment", "Purchase", "Subscription", "Transfer"]


def random_date(start: datetime, end: datetime) -> datetime:
    delta_secs = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta_secs))


def random_daytime_hour() -> int:
    """Return an hour between 6 AM and 11 PM (normal hours only)."""
    return random.randint(6, 23)


def generate_customer(cust_id: str, name: str, rule_type: str) -> dict:
    account_opened = datetime(2023, 1, 1)
    # 6-month history window gives a richer baseline
    end_date = datetime(2026, 6, 1)
    start_date = end_date - timedelta(days=180)

    txns = []
    num_txns = random.randint(90, 130)

    for i in range(num_txns):
        dt = random_date(start_date, end_date)
        dt = dt.replace(hour=random_daytime_hour(), minute=random.randint(0, 59), second=0)
        amt = round(random.uniform(500, 5000), 2)
        txns.append({
            "txn_id": f"T_{cust_id}_{i}",
            "date": dt.isoformat(),
            "description": random.choice(DESCRIPTIONS),
            "payee": random.choice(PAYEES),
            "amount": amt,
            "channel": random.choice(CHANNELS),
        })

    txns.sort(key=lambda x: x["date"])

    if rule_type == "rule1":
        # Rule 1: amount > max(4×median, ₹40,000). Typical median ~₹2,750 →
        # threshold = ₹40,000. Inject a ₹45,000 transfer near the end.
        txns[-1]["amount"] = 45_000.0
        txns[-1]["date"] = (end_date + timedelta(days=1)).replace(
            hour=10, minute=0, second=0
        ).isoformat()

    elif rule_type == "rule2":
        # Rule 2: a brand-new payee gets ≥3 transactions within 7 days,
        # and there are already ≥ RULE2_MIN_BASELINE (20) total transactions
        # before the burst so the "new payee" detection is meaningful.
        burst_start = end_date
        for i in range(3):
            dt = (burst_start + timedelta(days=i)).replace(
                hour=14, minute=0, second=0
            )
            txns.append({
                "txn_id": f"T_{cust_id}_burst_{i}",
                "date": dt.isoformat(),
                "description": "Transfer",
                "payee": "Swift Remittance Ltd",   # brand-new payee
                "amount": 2_000.0,
                "channel": "UPI",
            })

    elif rule_type == "rule3":
        # Rule 3: a transaction between 00:00–04:59 from a customer who has
        # never transacted in those hours before.
        dt = (end_date + timedelta(days=1)).replace(hour=2, minute=30, second=0)
        txns.append({
            "txn_id": f"T_{cust_id}_odd",
            "date": dt.isoformat(),
            "description": "Transfer",
            "payee": "Night Owl Traders",
            "amount": 1_500.0,
            "channel": "Credit Card",
        })

    elif rule_type == "multirule":
        # Rules 1 + 3: large amount AND odd hour in the same transaction.
        dt = (end_date + timedelta(days=1)).replace(hour=3, minute=15, second=0)
        txns.append({
            "txn_id": f"T_{cust_id}_multi",
            "date": dt.isoformat(),
            "description": "Transfer",
            "payee": "Horizon Capital",
            "amount": 55_000.0,
            "channel": "UPI",
        })

    txns.sort(key=lambda x: x["date"])

    return {
        "customer_id": cust_id,
        "name": name,
        "account_opened": account_opened.strftime("%Y-%m-%d"),
        "transactions": txns,
    }


def main():
    os.makedirs("data/customers", exist_ok=True)

    configs = [
        # (file_id, display_name,      rule_type)
        ("C001", "Aarav Shah",   "clean"),
        ("C002", "Priya Menon",  "rule1"),
        ("C003", "Rohan Iyer",   "rule2"),
        ("C004", "Sneha Kapoor", "rule3"),
        ("C005", "Vikram Nair",  "multirule"),
    ]

    for cust_id, name, rule_type in configs:
        data = generate_customer(cust_id, name, rule_type)
        path = f"data/customers/{cust_id}.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Written {path}  ({len(data['transactions'])} transactions, rule={rule_type})")


if __name__ == "__main__":
    main()
