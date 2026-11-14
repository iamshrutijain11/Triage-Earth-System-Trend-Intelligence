"""Streamlit deployment root entrypoint.

Directly launches the modern frontend presentation tier (frontend/app.py).
Enables one-click deployment to Streamlit Community Cloud, Hugging Face Spaces,
and containerized cloud services.
"""

import sys
from pathlib import Path

# Prepend project root and frontend/backend directories to sys.path
root_dir = Path(__file__).resolve().parent
for p in (str(root_dir), str(root_dir / "frontend"), str(root_dir / "backend")):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from frontend.app import main
except (ImportError, ModuleNotFoundError):
    from p4_app.app.main import main

if __name__ == "__main__":
    main()
