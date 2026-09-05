<div align="center">
  <h1>🛡️ Transaction Risk Investigation Assistant</h1>
  <p><strong>Intelligent detection and narrative synthesis for financial anomalies</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white" alt="Python Version" />
    <img src="https://img.shields.io/badge/FastAPI-005571?logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Google_Gemini-8E75B2?logo=google-gemini&logoColor=white" alt="Gemini" />
    <img src="https://img.shields.io/badge/Vercel-000000?logo=vercel&logoColor=white" alt="Vercel" />
  </p>
  
  <p><i>Track ID: <b>PS06</b></i></p>
</div>

<hr />

## 📖 Overview

The **Transaction Risk Investigation Assistant** is an intelligent web application designed to help fraud investigators rapidly assess customer activity. 

It uses a **two-layer architecture**:
1. **Deterministic Rule Engine (Layer A)**: Scans transaction history against predefined statistical thresholds and behavioral patterns to flag suspicious activity with high accuracy and zero hallucination.
2. **LLM Synthesis (Layer B)**: Leverages **Google Gemini** to ingest the raw structural findings and output a clear, human-readable narrative explaining *why* the transactions were flagged and what the investigator should do next.

## ✨ Features

- **📊 Deterministic Anomaly Detection**: 
  - Catches statistical outliers (z-score > 2.5).
  - Detects unusual odd-hour activities against baseline history.
  - Flags sudden transaction bursts to newly added payees.
- **🧠 Generative AI Reporting**: Translates cold data facts into professional investigation narratives using Gemini (with built-in fallback models for resilience).
- **💅 Elegant UI**: A snappy, modern dashboard featuring cross-fade animations, staggered list rendering, and clear visual hierarchy (Zero dependencies, pure CSS/JS).
- **⚡ Serverless Ready**: Fully configured for Vercel deployment with ASGI routing.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- A Google Gemini API key

### 1. Clone & Install
```bash
git clone https://github.com/sanjay2717/NexusiT0Transaction-Risk-Investigation.git
cd NexusiT0Transaction-Risk-Investigation
pip install -r requirements.txt
```

### 2. Configure Environment
Set your Gemini API key in your environment variables. If left unset, the application will gracefully fall back to a deterministic text-template report.
```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"

# Mac/Linux
export GEMINI_API_KEY="your_api_key_here"
```

### 3. Run the Server
```bash
python app.py
```
Visit **[http://localhost:8000](http://localhost:8000)** in your browser to view the dashboard!

---

## 📂 Project Structure

```text
.
├── app.py                  # Local FastAPI entry point
├── vercel.json             # Vercel deployment configuration
├── api/
│   └── index.py            # Serverless ASGI router for Vercel
├── src/
│   ├── api.py              # REST endpoints (/api/customers, /api/customers/*/report)
│   ├── models.py           # Pydantic data models
│   ├── rules.py            # Deterministic anomaly detection engine (Layer A)
│   └── llm_report.py       # Gemini integration & prompt engineering (Layer B)
├── frontend/
│   └── index.html          # Clean, zero-dependency dashboard UI
└── data/
    ├── generate_data.py    # Synthetic customer data generator script
    └── customers/          # Auto-generated JSON datasets for testing
```

---

## 🔍 The Rule Engine (Layer A)

The system currently evaluates transactions against the following baseline heuristics:

| Rule | Description |
| :--- | :--- |
| **Rule 1: Large Transfer** | Flags transactions exceeding `max(4× median, ₹40,000)`. |
| **Rule 2: Burst Activity** | Flags 3+ transactions within 7 days to a *brand new* payee (requires a baseline of 20+ prior transactions to avoid account-open noise). |
| **Rule 3: Odd-Hours** | Flags activity between `00:00 - 04:59` if the customer has zero prior history of transacting in that window. |
| **Rule 4: Stat Outlier** | Flags transactions whose amount exceeds a `2.5 z-score` deviation from the customer's mean (skips transactions already caught by Rule 1). |

---

## 🎬 Demo

**Demo Video Link:** *(Add your video link here)*