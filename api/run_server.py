"""
run_server.py — Convenience script to start the API from INSIDE the api/ directory.

Usage (from inside api/):
  python run_server.py

Or from the parent BLOG IMAGE CREATION/ directory:
  python -m uvicorn api.main:app --reload --port 8000
"""

import subprocess
import sys
from pathlib import Path

# We need to run uvicorn from the PARENT directory so relative imports work.
parent = Path(__file__).parent.parent

subprocess.run(
    [
        sys.executable, "-m", "uvicorn",
        "api.main:app",
        "--reload",
        "--port", "8000",
        "--host", "0.0.0.0",
    ],
    cwd=str(parent),
)
