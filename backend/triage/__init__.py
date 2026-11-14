"""
TRIAGE Tactical Disaster & Flood Response Engine.

Unified operational engine containing:
- fetch (Satellite SAR, optical, DEM, OSM data retrieval)
- detect (SAR change detection, coherence disturbance, U-Net flood segmentation, 4-way fusion)
- terrain (HAND, slope, radar shadow/layover exclusion)
- flowpath (D8 steepest descent flow routing)
- rescue (Dry islands, walking escape paths, landing zones / HLZ)
- damage (OSM building, road, and bridge damage overlay)
- network (Monte Carlo road network percolation cut-off)
- eval (Copernicus EMS EMSR927 validation)
- report (WeasyPrint Situation Reports and SMS transmission)
- pipeline (7-stage orchestrator)
"""

from backend.triage import fetch
from backend.triage import detect
from backend.triage import terrain
from backend.triage import flowpath
from backend.triage import rescue
from backend.triage import damage
from backend.triage import network
from backend.triage import eval
from backend.triage import report
from backend.triage.pipeline import run

__all__ = [
    "fetch",
    "detect",
    "terrain",
    "flowpath",
    "rescue",
    "damage",
    "network",
    "eval",
    "report",
    "run",
]
