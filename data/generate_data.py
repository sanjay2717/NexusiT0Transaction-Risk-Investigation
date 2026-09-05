import json
import random
from datetime import datetime, timedelta
import os

random.seed(42)

PAYEES = ["Grocery Store", "Electric Bill", "Amazon", "Local Restaurant", "Netflix", "Gas Station"]
CHANNELS = ["UPI", "Credit Card", "Debit Card", "Net Banking"]
DESCRIPTIONS = ["Payment", "Purchase", "Subscription", "Transfer"]

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def random_normal_hour():
    return random.randint(6, 23)

def generate_customer(cust_id, rule_type):
    account_opened = datetime(2023, 1, 1)
    end_date = datetime(2026, 6, 1)
    start_date = end_date - timedelta(days=120)
    
    txns = []
    num_txns = random.randint(80, 120)
    
    for i in range(num_txns):
        dt = random_date(start_date, end_date)
        dt = dt.replace(hour=random_normal_hour())
        amt = round(random.uniform(500, 5000), 2)
        txns.append({
            "txn_id": f"T_{cust_id}_{i}",
            "date": dt.isoformat(),
            "description": random.choice(DESCRIPTIONS),
            "payee": random.choice(PAYEES),
            "amount": amt,
            "channel": random.choice(CHANNELS)
        })
    
    txns.sort(key=lambda x: x["date"])
    
    if rule_type == "rule1":
        # Rule 1: amount > max(4x median, 40000). Median ~2750.
        txns[-1]["amount"] = 45000.0
        txns[-1]["date"] = (end_date + timedelta(days=1)).replace(hour=10).isoformat()
        
    elif rule_type == "rule2":
        # Rule 2: burst to new payee. >=3 txns in 7 days to new payee.
        burst_start = end_date
        for i in range(3):
            dt = burst_start + timedelta(days=i)
            dt = dt.replace(hour=14)
            txns.append({
                "txn_id": f"T_{cust_id}_burst_{i}",
                "date": dt.isoformat(),
                "description": "Transfer",
                "payee": "Unknown Entity",
                "amount": 2000.0,
                "channel": "UPI"
            })
            
    elif rule_type == "rule3":
        # Rule 3: odd-hours activity (12 AM - 5 AM)
        dt = end_date + timedelta(days=1)
        dt = dt.replace(hour=2, minute=30)
        txns.append({
            "txn_id": f"T_{cust_id}_odd",
            "date": dt.isoformat(),
            "description": "Transfer",
            "payee": "Late Night Diner",
            "amount": 1500.0,
            "channel": "Credit Card"
        })
        
    elif rule_type == "multirule":
        # Rules 1 and 3
        dt = end_date + timedelta(days=1)
        dt = dt.replace(hour=3, minute=15)
        txns.append({
            "txn_id": f"T_{cust_id}_multi",
            "date": dt.isoformat(),
            "description": "Transfer",
            "payee": "Shady Business",
            "amount": 55000.0,
            "channel": "UPI"
        })
        
    txns.sort(key=lambda x: x["date"])
    
    return {
        "customer_id": cust_id,
        "account_opened": account_opened.strftime("%Y-%m-%d"),
        "transactions": txns
    }

def main():
    os.makedirs("data/customers", exist_ok=True)
    
    configs = [
        ("C001", "clean"),
        ("C002", "rule1"),
        ("C003", "rule2"),
        ("C004", "rule3"),
        ("C005", "multirule"),
    ]
    
    for cust_id, rule_type in configs:
        data = generate_customer(cust_id, rule_type)
        with open(f"data/customers/{cust_id}_{rule_type}.json", "w") as f:
            json.dump(data, f, indent=2)
            
if __name__ == "__main__":
    main()
