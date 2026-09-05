import json
import os
import glob
from fastapi import APIRouter, HTTPException
from src.models import Customer
from src.rules import get_all_findings
from src.llm_report import generate_report

router = APIRouter()

DATA_DIR = os.path.join("data", "customers")

def get_customer_data(cust_id: str):
    files = glob.glob(os.path.join(DATA_DIR, f"{cust_id}_*.json"))
    if not files:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    with open(files[0], 'r') as f:
        data = json.load(f)
        
    valid_txns = []
    for t in data.get('transactions', []):
        try:
            if 'txn_id' in t and 'amount' in t and 'date' in t:
                valid_txns.append(t)
            else:
                print(f"Skipping malformed transaction in {cust_id}")
        except Exception:
            pass
    data['transactions'] = valid_txns
    
    return Customer(**data)

@router.get("/api/customers")
def list_customers():
    customers = []
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".json"):
                parts = filename.replace(".json", "").split("_", 1)
                cust_id = parts[0]
                name = filename.replace(".json", "")
                customers.append({"id": cust_id, "name": name})
    return sorted(customers, key=lambda x: x["id"])

@router.get("/api/customers/{cust_id}/report")
def get_customer_report(cust_id: str):
    customer = get_customer_data(cust_id)
    findings = get_all_findings(customer)
    verdict, narrative = generate_report(findings)
    
    findings_dict = []
    for f in findings:
        if hasattr(f, 'model_dump'):
            findings_dict.append(f.model_dump())
        else:
            findings_dict.append(f.dict())
            
    return {
        "verdict": verdict,
        "findings": findings_dict,
        "narrative": narrative
    }
