import os
import json
import google.generativeai as genai
from typing import List, Tuple
from src.models import Finding

def generate_report(findings: List[Finding]) -> Tuple[str, str]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found, using fallback report.")
        return generate_fallback_report(findings)
        
    genai.configure(api_key=api_key)
        
    prompt = _build_prompt(findings)
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt) 
        
        text = response.text.strip()
        lines = text.split('\n')
        verdict = lines[0].strip()
        narrative = '\n'.join(lines[1:]).strip()
        
        return verdict, narrative
    except Exception as e:
        print(f"Gemini call failed: {e}")
        return generate_fallback_report(findings)

def _build_prompt(findings: List[Finding]) -> str:
    # Use standard dict serialization for Pydantic v2 support
    findings_json = []
    for f in findings:
        # Fallback to model_dump() or dict() depending on pydantic version
        if hasattr(f, 'model_dump'):
            findings_json.append(f.model_dump())
        else:
            findings_json.append(f.dict())
            
    findings_str = json.dumps(findings_json, indent=2)
    
    return f"""You are a Transaction Risk Investigation Assistant.
    
You are given ONLY a structured findings object for one customer — no raw transaction history beyond what's listed as evidence.

Structured Findings:
{findings_str}

Instructions:
1. Never state or imply fraud has occurred. Use language like "warrants review," "worth investigating," never "is fraudulent."
2. Lead with the verdict as the VERY FIRST LINE of your response: either "No findings — this history looks consistent with the customer's established pattern" or "N finding(s) identified." (replace N with the actual count).
3. Then provide the narrative. For each finding: which rule, which transactions (cite txn_ids exactly as given), how it differs from this customer's normal pattern (use the summary_facts you were given), and one concrete next step for the investigator.
4. Do not invent any transaction ID not present in the evidence you were given.
5. If findings list is empty, say so plainly in 1-2 sentences. Do not manufacture concern.
"""

def generate_fallback_report(findings: List[Finding]) -> Tuple[str, str]:
    if not findings:
        verdict = "No findings — this history looks consistent with the customer's established pattern"
        narrative = "The rule engine found no anomalies. System fell back to template due to LLM timeout/error."
        return verdict, narrative
        
    verdict = f"{len(findings)} finding(s) identified."
    lines = ["System generated fallback report (LLM unavailable):"]
    for i, f in enumerate(findings, 1):
        lines.append(f"\nFinding {i}: {f.rule_id}")
        lines.append(f"Evidence Transactions: {', '.join(f.evidence)}")
        lines.append(f"Summary Facts: {json.dumps(f.summary_facts)}")
        lines.append("Next Step: Investigator to review above transactions manually.")
        
    return verdict, "\n".join(lines)
