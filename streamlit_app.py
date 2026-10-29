"""Streamlit deployment root entrypoint.

Enables one-click deployment to Streamlit Community Cloud, Hugging Face Spaces,
and containerized cloud services.
"""

import sys
from pathlib import Path

# Prepend project root to sys.path
root_dir = Path(__file__).resolve().parent
for p in (str(root_dir), str(root_dir / "p4_app"), str(root_dir / "app")):
    if p not in sys.path:
        sys.path.insert(0, p)

from p4_app.app.main import main

if __name__ == "__main__":
    main()

