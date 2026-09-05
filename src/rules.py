import statistics
from datetime import datetime, timedelta
from typing import List
from src.models import Customer, Transaction, Finding

RULE1_MULTIPLIER = 4.0
RULE1_FLOOR = 40000.0

RULE2_COUNT = 3
RULE2_DAYS = 7

RULE3_START_HOUR = 0
RULE3_END_HOUR = 5

RULE4_ZSCORE = 2.5
MIN_HISTORY = 10

def check_rule_1(customer: Customer) -> Finding:
    if not customer.transactions:
        return Finding(rule_id="Rule 1", triggered=False, evidence=[], summary_facts={})
    
    amounts = [t.amount for t in customer.transactions]
    median_amt = statistics.median(amounts)
    threshold = max(RULE1_MULTIPLIER * median_amt, RULE1_FLOOR)
    
    for t in reversed(customer.transactions):
        if t.amount > threshold:
            return Finding(
                rule_id="Rule 1",
                triggered=True,
                evidence=[t.txn_id],
                summary_facts={
                    "median_amount": median_amt,
                    "threshold": threshold,
                    "transaction_amount": t.amount
                }
            )
            
    return Finding(rule_id="Rule 1", triggered=False, evidence=[], summary_facts={"median_amount": median_amt, "threshold": threshold})

def check_rule_2(customer: Customer) -> Finding:
    payee_txns = {}
    for t in customer.transactions:
        if t.payee not in payee_txns:
            payee_txns[t.payee] = []
        payee_txns[t.payee].append(t)
        
    for payee, txns in payee_txns.items():
        if len(txns) >= RULE2_COUNT:
            txns = sorted(txns, key=lambda x: x.date)
            # Only consider it a "newly added payee" if the first 3 transactions occur within 7 days.
            if len(txns) >= RULE2_COUNT:
                window = txns[:RULE2_COUNT]
                time_diff = window[-1].date - window[0].date
                if time_diff <= timedelta(days=RULE2_DAYS):
                    return Finding(
                        rule_id="Rule 2",
                        triggered=True,
                        evidence=[w.txn_id for w in window],
                        summary_facts={
                            "payee": payee,
                            "burst_count": len(window),
                            "time_window_days": time_diff.days
                        }
                    )
    return Finding(rule_id="Rule 2", triggered=False, evidence=[], summary_facts={})

def check_rule_3(customer: Customer) -> Finding:
    first_odd_idx = -1
    for i, t in enumerate(customer.transactions):
        hour = t.date.hour
        if RULE3_START_HOUR <= hour < RULE3_END_HOUR or (hour == RULE3_END_HOUR and t.date.minute == 0):
            if first_odd_idx == -1:
                first_odd_idx = i
                break
                
    if first_odd_idx != -1:
        t = customer.transactions[first_odd_idx]
        if first_odd_idx >= MIN_HISTORY:
             return Finding(
                rule_id="Rule 3",
                triggered=True,
                evidence=[t.txn_id],
                summary_facts={
                    "transaction_time": t.date.isoformat(),
                    "total_prior_transactions": first_odd_idx
                }
            )
            
    return Finding(rule_id="Rule 3", triggered=False, evidence=[], summary_facts={})

def check_rule_4(customer: Customer) -> Finding:
    if len(customer.transactions) < MIN_HISTORY:
        return Finding(rule_id="Rule 4", triggered=False, evidence=[], summary_facts={"reason": "baseline is too thin for pattern analysis"})
        
    amounts = [t.amount for t in customer.transactions]
    mean_amt = statistics.mean(amounts)
    median_amt = statistics.median(amounts)
    stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
    seen_channels = set()
    
    for i, t in enumerate(customer.transactions):
        if stdev > 0:
            z_score = (t.amount - mean_amt) / stdev
            if z_score > RULE4_ZSCORE:
                contrast = [x.txn_id for x in customer.transactions if x.amount <= median_amt][:2]
                return Finding(
                    rule_id="Rule 4",
                    triggered=True,
                    evidence=[t.txn_id] + contrast,
                    summary_facts={
                        "z_score": z_score,
                        "mean": mean_amt,
                        "stdev": stdev
                    }
                )
                
        if i >= MIN_HISTORY and t.channel not in seen_channels and t.amount > median_amt:
             contrast = [x.txn_id for x in customer.transactions[:2]]
             return Finding(
                rule_id="Rule 4",
                triggered=True,
                evidence=[t.txn_id] + contrast,
                summary_facts={
                    "new_channel": t.channel,
                    "amount": t.amount,
                    "median_amount": median_amt
                }
            )
            
        seen_channels.add(t.channel)
        
    return Finding(rule_id="Rule 4", triggered=False, evidence=[], summary_facts={})

def get_all_findings(customer: Customer) -> List[Finding]:
    findings = []
    for rule in [check_rule_1, check_rule_2, check_rule_3, check_rule_4]:
        f = rule(customer)
        if f.triggered:
            findings.append(f)
    return findings

if __name__ == '__main__':
    from datetime import date
    
    # Inline tests for Rule 1 boundaries
    base_txns = [
        Transaction(txn_id=f"T{i}", date=datetime(2026, 1, 1), description="test", payee="test", amount=1000.0, channel="UPI")
        for i in range(10)
    ]
    c1 = Customer(customer_id="C1", account_opened=date(2023,1,1), transactions=base_txns + [
        Transaction(txn_id="T_below", date=datetime(2026,1,2), description="test", payee="test", amount=39999.0, channel="UPI")
    ])
    assert not check_rule_1(c1).triggered, "Rule 1 should not trigger below 40000"

    c2 = Customer(customer_id="C2", account_opened=date(2023,1,1), transactions=base_txns + [
        Transaction(txn_id="T_above", date=datetime(2026,1,2), description="test", payee="test", amount=40001.0, channel="UPI")
    ])
    assert check_rule_1(c2).triggered, "Rule 1 should trigger above 40000"

    # Inline tests for Rule 3 boundaries
    c3_txns = base_txns.copy()
    c3_txns.append(Transaction(txn_id="T_5_01", date=datetime(2026,1,2,5,1), description="test", payee="test", amount=1000.0, channel="UPI"))
    c3 = Customer(customer_id="C3", account_opened=date(2023,1,1), transactions=c3_txns)
    assert not check_rule_3(c3).triggered, "5:01 AM should not trigger odd hours"

    c4_txns = base_txns.copy()
    c4_txns.append(Transaction(txn_id="T_4_59", date=datetime(2026,1,2,4,59), description="test", payee="test", amount=1000.0, channel="UPI"))
    c4 = Customer(customer_id="C4", account_opened=date(2023,1,1), transactions=c4_txns)
    assert check_rule_3(c4).triggered, "4:59 AM should trigger odd hours"
    print("Tests passed.")
