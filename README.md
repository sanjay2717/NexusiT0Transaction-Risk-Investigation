TRACK_ID=PS06
Transaction Risk Investigation Assistant
This application analyzes customer transaction histories and flags potential risks for human review. It utilizes a deterministic rule engine to find anomalies like unusually large transfers or odd-hour activities, and a Gemini LLM to synthesize these findings into a coherent narrative.
How to run (pip install -r requirements.txt && python app.py, then http://localhost:8000)
Synthetic data including 5 test customers covering clean and rule-triggered edge cases was generated using a custom script located at data/generate_data.py.
Env vars needed: GEMINI_API_KEY
Demo video link: <fill in>