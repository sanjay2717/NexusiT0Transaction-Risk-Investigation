import os
import json
import traceback
from typing import List, Tuple
from src.models import Finding

def generate_report(findings: List[Finding]) -> Tuple[str, str]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[llm_report] No GEMINI_API_KEY in environment — using fallback template.")
        return generate_fallback_report(findings)

    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        prompt = _build_prompt(findings)

        _MODELS = ["gemini-3.6-flash", "gemini-3.5-flash"]
        response = None
        used_model = None

        for model_name in _MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                used_model = model_name
                print(f"[llm_report] Successfully generated report using {model_name}")
                break
            except Exception as model_err:
                err_type = type(model_err).__name__
                err_msg = str(model_err)
                if "NotFound" in err_type or "404" in err_msg:
                    print(f"[llm_report] {model_name} not available: {err_msg[:120]}")
                    continue  # try next model in chain
                raise  # re-raise non-NotFound errors immediately

        if response is None:
            print(f"[llm_report] All models in chain unavailable — using fallback template.")
            return generate_fallback_report(findings)

        text = response.text.strip()
        lines = text.split("\n")
        verdict = lines[0].strip()
        narrative = "\n".join(lines[1:]).strip()
        return verdict, narrative


    except ImportError as e:
        print(f"[llm_report] ImportError — SDK not installed: {type(e).__name__}: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"[llm_report] Gemini call failed: {type(e).__name__}: {e}")
        traceback.print_exc()

    return generate_fallback_report(findings)


def _build_prompt(findings: List[Finding]) -> str:
    findings_json = [
        f.model_dump() if hasattr(f, "model_dump") else f.dict()
        for f in findings
    ]
    findings_str = json.dumps(findings_json, indent=2)

    return f"""You are a Transaction Risk Investigation Assistant.

You are given ONLY a structured findings object for one customer — no raw \
transaction history beyond what is listed as evidence.

Structured Findings:
{findings_str}

Instructions:
1. Never state or imply fraud has occurred. Use language like "warrants review," \
"worth investigating," never "is fraudulent."
2. The VERY FIRST LINE of your response must be the verdict:
   - If no findings: "No findings — this history looks consistent with the customer's established pattern"
   - Otherwise: "N finding(s) identified." (replace N with the actual count)
3. For each finding: state which rule, cite txn_ids exactly as given in evidence, \
explain how it differs from the customer's normal pattern using summary_facts, \
and suggest one concrete next step for the investigator.
4. Do not invent any transaction ID not present in the evidence you were given.
5. If findings list is empty, say so in 1-2 sentences. Do not manufacture concern.
6. Write full sentences for the narrative. Never output raw JSON, dict syntax, or key:value pairs in the narrative.
"""


def _format_summary_facts(f: Finding) -> str:
    facts = f.summary_facts
    rule = f.rule_id

    if rule == "Rule 1":
        tx_amt = facts.get('transaction_amount', 0)
        median = facts.get('median_amount', 1)
        multiplier = round(tx_amt / median) if median else 0
        return f"This transaction of ₹{tx_amt:,.2f} is roughly {multiplier}x this customer's typical transaction amount of ₹{median:,.2f}."
    
    elif rule == "Rule 2":
        return f"This customer made {facts.get('burst_count')} transactions to a newly added payee '{facts.get('payee')}' within a {facts.get('time_window_days')}-day window, after {facts.get('baseline_txns')} prior transactions with no history to this payee."
    
    elif rule == "Rule 3":
        dt_str = facts.get('transaction_time', '')
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(dt_str)
            time_str = dt.strftime("%I:%M %p on %Y-%m-%d")
        except:
            time_str = dt_str
        return f"This transaction occurred at {time_str}. This customer has no history of transacting during odd hours (0 of their prior {facts.get('total_prior_transactions')} transactions)."
        
    elif rule == "Rule 4":
        return f"This transaction amount of ₹{facts.get('transaction_amount', 0):,.2f} deviates significantly from the customer's typical range (z-score: {facts.get('z_score')}, mean: ₹{facts.get('mean', 0):,.2f})."
        
    return json.dumps(facts)


def generate_fallback_report(findings: List[Finding]) -> Tuple[str, str]:
    if not findings:
        verdict = "No findings — this history looks consistent with the customer's established pattern"
        narrative = (
            "The deterministic rule engine found no anomalies in this customer's history."
        )
        return verdict, narrative

    verdict = f"{len(findings)} finding(s) identified."
    lines = ["[Fallback report — LLM unavailable]\n"]
    for i, f in enumerate(findings, 1):
        lines.append(f"Finding {i}: {f.rule_id}")
        lines.append(f"  Evidence transactions : {', '.join(f.evidence)}")
        lines.append(f"  Summary facts         : {_format_summary_facts(f)}")
        lines.append("  Recommended action    : Investigator should manually review the above transactions.\n")

    return verdict, "\n".join(lines)
