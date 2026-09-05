import json
import os
import glob
from fastapi import APIRouter, HTTPException
from src.models import Customer
from src.rules import get_all_findings
from src.llm_report import generate_report

router = APIRouter()

# Anchor to repo root so paths resolve correctly under both
# `python app.py` (CWD=root) and Vercel's serverless runner.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_REPO_ROOT, "data", "customers")


def _load_file(cust_id: str) -> dict:
    """Load customer JSON by ID. Supports both C001.json and legacy C001_*.json."""
    # Prefer exact match first (new naming), fall back to wildcard (old naming)
    exact = os.path.join(DATA_DIR, f"{cust_id}.json")
    if os.path.exists(exact):
        path = exact
    else:
        matches = glob.glob(os.path.join(DATA_DIR, f"{cust_id}_*.json"))
        if not matches:
            raise HTTPException(status_code=404, detail=f"Customer '{cust_id}' not found")
        path = matches[0]

    with open(path, "r") as f:
        return json.load(f)


def get_customer_data(cust_id: str) -> Customer:
    data = _load_file(cust_id)

    # Sanitise transactions: skip any record missing required fields
    required = {"txn_id", "date", "description", "payee", "amount", "channel"}
    valid_txns = []
    for t in data.get("transactions", []):
        try:
            if required.issubset(t.keys()):
                valid_txns.append(t)
            else:
                missing = required - t.keys()
                print(f"[api] Skipping malformed txn in {cust_id}: missing {missing}")
        except Exception as exc:
            print(f"[api] Error parsing txn in {cust_id}: {exc}")

    data["transactions"] = valid_txns

    # Strip non-model fields before constructing Customer
    customer_fields = {"customer_id", "account_opened", "transactions"}
    clean = {k: v for k, v in data.items() if k in customer_fields}
    return Customer(**clean)


@router.get("/api/customers")
def list_customers():
    """Return list of {id, name} for the customer picker."""
    customers = []
    if not os.path.exists(DATA_DIR):
        return customers

    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(DATA_DIR, filename)
        try:
            with open(path) as f:
                raw = json.load(f)
            cust_id = raw.get("customer_id", filename.replace(".json", ""))
            # Use the name field if present; fall back to customer_id
            name = raw.get("name", cust_id)
            customers.append({"id": cust_id, "name": name})
        except Exception as exc:
            print(f"[api] Could not read {filename}: {exc}")

    return sorted(customers, key=lambda x: x["id"])


@router.get("/api/customers/{cust_id}/report")
def get_customer_report(cust_id: str):
    customer = get_customer_data(cust_id)
    findings = get_all_findings(customer)
    verdict, narrative = generate_report(findings)

    findings_dict = [
        f.model_dump() if hasattr(f, "model_dump") else f.dict()
        for f in findings
    ]

    return {
        "verdict": verdict,
        "findings": findings_dict,
        "narrative": narrative,
    }
