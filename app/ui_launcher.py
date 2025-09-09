from __future__ import annotations

import os
import sys
from pathlib import Path

def main() -> None:
    """Launch Streamlit app via CLI (stable across versions)."""
    target = str(Path(__file__).parent / "streamlit_app.py")
    # Use the current venv's Python to run "python -m streamlit run <app>"
    if not os.path.exists(target):
        raise SystemExit(f"App not found: {target}")
    os.execv(sys.executable, [sys.executable, "-m", "streamlit", "run", target])