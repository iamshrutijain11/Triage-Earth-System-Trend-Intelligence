"""
TRIAGE — Earth System Trend Intelligence & Impact Explorer
Statistical Trend-Analysis Engine

A scientifically rigorous, reproducible statistical engine for analyzing
Earth-science time series from NASA observations. Implements:

- Time-series generation and missing-data analysis
- Seasonal decomposition and anomaly calculation
- Sen's slope estimation with proper time units
- Mann-Kendall and Seasonal Mann-Kendall significance testing
- Serial autocorrelation detection and correction
- Confidence interval calculation
- Multiple hypothesis testing correction (FDR/Bonferroni)
- Trend direction classification and interpretation
- Climate trend impact coupling to physical hazard infrastructure

Designed for NASA Space Apps 2026: "Be An Earth System Trend Detective!"
"""

__version__ = "1.0.0"

from trend_engine.models import TrendResult, VisualizationData
from trend_engine.analyzer import TrendAnalyzer
from trend_engine.api import analyze_variable, compare_regions, analyze_spatial_grid
from trend_engine.impact import ImpactAssessment, assess_climate_trend_impact

__all__ = [
    "TrendAnalyzer",
    "TrendResult",
    "VisualizationData",
    "ImpactAssessment",
    "analyze_variable",
    "compare_regions",
    "analyze_spatial_grid",
    "assess_climate_trend_impact",
]
