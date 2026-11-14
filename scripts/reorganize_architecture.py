"""
Script to create the clean frontend/ and backend/ architecture while maintaining
full backward compatibility.
"""

import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
backend = root / "backend"
frontend = root / "frontend"

backend.mkdir(exist_ok=True)
frontend.mkdir(exist_ok=True)

# 1. Create backend/__init__.py
(backend / "__init__.py").write_text('"""TRIAGE Backend Core Computing Tier."""\n', encoding="utf-8")

# 2. Copy shared -> backend/shared
if (root / "shared").exists():
    shutil.copytree(root / "shared", backend / "shared", dirs_exist_ok=True)

# 3. Copy nasa_data -> backend/nasa_data
if (root / "nasa_data").exists():
    shutil.copytree(root / "nasa_data", backend / "nasa_data", dirs_exist_ok=True)

# 4. Copy trend_engine -> backend/trend_engine
if (root / "trend_engine").exists():
    shutil.copytree(root / "trend_engine", backend / "trend_engine", dirs_exist_ok=True)

# 5. Assemble backend/triage
triage_dir = backend / "triage"
triage_dir.mkdir(exist_ok=True)
(triage_dir / "__init__.py").write_text('"""Tactical Disaster and Flood Response Engine."""\n', encoding="utf-8")

# Copy p1_data parts
shutil.copytree(root / "p1_data" / "fetch", triage_dir / "fetch", dirs_exist_ok=True)
shutil.copytree(root / "p1_data" / "offline", triage_dir / "offline", dirs_exist_ok=True)
shutil.copy2(root / "p1_data" / "pipeline.py", triage_dir / "pipeline.py")

# Copy p2_ai parts
shutil.copytree(root / "p2_ai" / "detect", triage_dir / "detect", dirs_exist_ok=True)

# Copy p3_terrain parts
shutil.copytree(root / "p3_terrain" / "flowpath", triage_dir / "flowpath", dirs_exist_ok=True)
shutil.copytree(root / "p3_terrain" / "rescue", triage_dir / "rescue", dirs_exist_ok=True)
shutil.copytree(root / "p3_terrain" / "terrain", triage_dir / "terrain", dirs_exist_ok=True)

# Copy p4_app parts
shutil.copytree(root / "p4_app" / "damage", triage_dir / "damage", dirs_exist_ok=True)
shutil.copytree(root / "p4_app" / "eval", triage_dir / "eval", dirs_exist_ok=True)
shutil.copytree(root / "p4_app" / "network", triage_dir / "network", dirs_exist_ok=True)
shutil.copytree(root / "p4_app" / "report", triage_dir / "report", dirs_exist_ok=True)

# 6. Assemble frontend
(frontend / "__init__.py").write_text('"""TRIAGE Frontend Web Presentation Tier."""\n', encoding="utf-8")
shutil.copy2(root / "p4_app" / "app" / "main.py", frontend / "app.py")
shutil.copy2(root / "p4_app" / "app" / "components.py", frontend / "components.py")
shutil.copytree(root / "p4_app" / "app" / "views", frontend / "views", dirs_exist_ok=True)

print("SUCCESS: frontend/ and backend/ directories structured cleanly.")
