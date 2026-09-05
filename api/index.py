"""
Vercel entry point — imports the same FastAPI `app` from app.py
and re-exports it as `app` for Vercel's ASGI runner.

All path resolution happens relative to the repo root, which Vercel
sets as the working directory for serverless function invocations.
The local `python app.py` path is completely unchanged.
"""
import sys
import os

# Ensure the repo root is on sys.path so `from src.xxx import ...` works
# the same way it does when you run `python app.py` from the root.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import the FastAPI instance built in app.py — no duplication.
from app import app  # noqa: F401  (re-exported as `app` for Vercel)
