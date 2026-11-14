"""
TRIAGE Backend Core Computing Tier.

Unified backend integrating:
- NASA Earth Observation Data Acquisition Layer (backend.nasa_data)
- Statistical Climatology Trend-Analysis Engine (backend.trend_engine)
- Tactical Disaster & Flood Response Engine (backend.triage)
- Common Geospatial Math and Grid Transforms (backend.shared)
"""

from backend import nasa_data
from backend import trend_engine
from backend import triage
from backend import shared

__all__ = ["nasa_data", "trend_engine", "triage", "shared"]
