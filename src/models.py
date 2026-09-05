from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime, date

class Transaction(BaseModel):
    txn_id: str
    date: datetime
    description: str
    payee: str
    amount: float
    channel: str

class Customer(BaseModel):
    customer_id: str
    account_opened: date
    transactions: List[Transaction]

class Finding(BaseModel):
    rule_id: str
    triggered: bool
    evidence: List[str]
    summary_facts: Dict[str, Any]

class ReportResponse(BaseModel):
    verdict: str
    findings: List[Finding]
    narrative: str
