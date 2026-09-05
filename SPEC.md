# PS06 — Transaction Risk Investigation Assistant
Reference spec for build. Paste this whole file into any AI assistant as context if you need to switch tools mid-build.

## TRACK_ID=PS06

## 1. What the system does (restated precisely)
Input: one customer's transaction history (date, description, payee, amount, channel) spanning several months.
Output: an investigation report whose **first line is a verdict** — "nothing needs attention" or "N items need attention" — followed by, for each flagged item:
- the specific transactions involved and how they connect
- which rule was triggered
- how the activity differs from that customer's own established pattern
- what an investigator should look at first

Hard constraints from the problem statement:
- Never state that fraud occurred. Flag, explain, hand judgement to a human.
- Every transaction cited must be traceable to the input history (no invented transaction IDs).
- A clean customer must come back clean — do not force a finding.

## 2. Submission constraints (do not violate these)
- `app.py` at repo root. `pip install -r requirements.txt` then `python app.py` starts backend + frontend together on **port 8000**.
- App must be answering requests within **90 seconds** of start. Any single request must respond within **60 seconds**.
- Only external API: Gemini, read from `GEMINI_API_KEY` env var. Never commit a key.
- No other network calls. No hosted vector DB. (We are not using a vector DB at all — see Design Decision below.)
- Repo root fixed shape: `app.py`, `requirements.txt`, `README.md` at root. Everything else your choice.
- README's first line, exactly: `TRACK_ID=PS06` — nothing else on that line.
- Commit your generated data. Do not commit venvs, model weights, or keys.
- Real commit history across the build — not one final dump. Commit after each milestone below.

## 3. Design decision: no RAG / no embeddings
This track's "knowledge" is a small, fixed rule set (4 rules), not a document corpus. There is nothing to retrieve.
Grounding here means: the LLM only ever sees pre-computed, structured findings from the deterministic rule engine — never raw history — so it cannot invent a transaction that wasn't flagged by a rule.
Do not add FAISS/Chroma/embeddings. It adds build time and demonstrates nothing for this problem.

## 4. Architecture — two layers, kept strictly separate (this separation IS a graded criterion)

**Layer A — Deterministic rule engine (pure Python, zero LLM calls, unit-testable)**
Input: one customer's transaction list (JSON).
Output: structured findings — a list of `{rule_id, triggered: bool, evidence: [transaction_ids], summary_facts: {...}}`.

**Layer B — LLM narrative synthesis (single Gemini call per report)**
Input: ONLY Layer A's structured output (never raw transactions).
Output: the human-readable report text, verdict-first, grounded to the evidence IDs it was given.

If the Gemini call fails or times out: fall back to a templated report built directly from Layer A's structured output (no narrative prose, just the facts). This satisfies "graceful behaviour when a model call fails" — do not let the whole request 500 if Gemini is down.

## 5. Data model

```json
// One transaction
{
  "txn_id": "T00042",
  "date": "2026-06-14T02:13:00",
  "description": "UPI transfer",
  "payee": "Ramesh Textiles",
  "amount": 48500.00,
  "channel": "UPI"
}
```

```json
// One customer file
{
  "customer_id": "C001",
  "account_opened": "2023-01-10",
  "transactions": [ /* 60-150 transactions across 3-6 months */ ]
}
```

## 6. The four rules — exact logic

1. **Unusually large transfer**: amount > max(4x customer's median transaction amount, a flat floor e.g. ₹40,000). Evidence = that single transaction.
2. **Burst to a newly added payee**: a payee with no prior transactions in the customer's history receives ≥3 transactions within a 7-day window. Evidence = all transactions to that payee in the burst window.
3. **Odd-hours activity**: transaction timestamp between 12:00 AM–5:00 AM local time, AND this customer has no prior history of transacting in that window (compare against their historical hour distribution). Evidence = the odd-hour transaction(s).
4. **Pattern deviation**: a transaction's amount is a statistical outlier vs. this customer's own history — e.g. z-score > 2.5 against their historical amount distribution, or a category/channel never used before combined with an above-median amount. Evidence = the deviating transaction + 2-3 representative "normal" transactions for contrast.

Each rule must state its own precise threshold in the code as a constant, not a magic number buried in logic — a judge should be able to read the rule and see exactly what it checks.

## 7. LLM prompt contract (Layer B)

System instruction (paraphrase, adapt in code):
- You are given ONLY a structured findings object for one customer — no raw transaction history beyond what's listed as evidence.
- Never state or imply fraud has occurred. Use language like "warrants review," "worth investigating," never "is fraudulent."
- Lead with the verdict: either "No findings — this history looks consistent with the customer's established pattern" or "N finding(s) identified."
- For each finding: which rule, which transactions (cite txn_ids exactly as given), how it differs from this customer's normal pattern (use the summary_facts you were given), and one concrete next step for the investigator.
- Do not invent any transaction ID not present in the evidence you were given.
- If findings list is empty, say so plainly in 1-2 sentences. Do not manufacture concern.

## 8. API surface (FastAPI, served from app.py)

- `GET /` → minimal HTML frontend (customer picker + report view)
- `GET /api/customers` → list of synthetic customer IDs + names for the picker
- `GET /api/customers/{id}/report` → runs Layer A then Layer B, returns JSON: `{verdict, findings: [...], narrative}`
- Frontend just fetches this and renders it. No build step — plain HTML/JS, no React, to avoid a second terminal/build requirement.

## 9. Synthetic data to generate (commit to `data/`)

Minimum 5 customers:
- 1 fully clean customer (no rule fires) — this is not optional, it's graded.
- 1 customer triggering exactly rule 1 only.
- 1 customer triggering exactly rule 2 only.
- 1 customer triggering rule 3 or 4 only.
- 1 customer triggering 2+ rules at once (the "hard" demo case).

Generate via a script (can use Gemini once at data-gen time, or hand-write) — 60-150 transactions per customer across 3-6 months so the "established pattern" baseline is real, not thin.

## 10. Edge cases to explicitly handle (this is graded — "incomplete, ambiguous, edge cases" not just happy path)
- Customer with very short history (<10 transactions) — pattern-deviation rule can't reliably fire; report should say baseline is too thin for pattern analysis rather than guessing.
- Malformed/missing fields in a transaction — skip that transaction, log it, don't crash the request.
- Gemini call timeout/error — fall back per Section 4.
- Borderline threshold values (e.g. amount at 3.9x median) — should NOT fire; verify rule boundaries with a test case just below and just above threshold.

## 11. File structure

```
app.py
requirements.txt
README.md
src/
  rules.py          # Layer A, pure functions, unit-testable
  llm_report.py      # Layer B, Gemini call + fallback template
  models.py           # pydantic schemas for transaction/customer/finding
  api.py                # FastAPI routes
data/
  customers/*.json    # 5 synthetic customer files
  generate_data.py    # script used to produce them (commit this too)
frontend/
  index.html
  app.js
```

## 12. README.md required shape
```
TRACK_ID=PS06
<project name>
What it does (2-3 sentences)
How to run (pip install -r requirements.txt && python app.py, then http://localhost:8000)
What data you generated and how (point to data/generate_data.py)
Env vars needed: GEMINI_API_KEY
Demo video link: <fill in>
```

## 13. Demo video (2-3 min) — what to actually show
1. Start with `python app.py` from a fresh clone, showing it comes up.
2. Pick the clean customer → show "no findings" verdict rendered plainly.
3. Pick the multi-rule customer (the hard case) → walk through the findings, point out the evidence transaction IDs match what's in the JSON, and that the language never claims fraud, only flags for review.

## 14. Grading criteria checklist — map before submitting
- [ ] `python app.py` runs from a truly fresh clone, no manual steps
- [ ] Real incremental commits exist (not one dump)
- [ ] Layer A and Layer B are in separate files with no LLM calls inside Layer A
- [ ] Every cited transaction ID exists in the input JSON
- [ ] Clean customer returns a clean verdict
- [ ] Gemini failure doesn't crash the request
- [ ] README starts with `TRACK_ID=PS06` on its own line, nothing else on that line