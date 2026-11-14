"""
Visualization data generators.

Produces structured data bundles for rendering:
- Historical time-series charts with trend lines
- Anomaly charts
- Regional comparisons
- Confidence interval bands
- Geographical trend maps
"""

from __future__ import annotations

import numpy as np
from typing import List, Optional

from trend_engine.models import TrendResult, VisualizationData
from trend_engine.trends import sens_slope, linear_trend
from trend_engine.decomposition import calculate_anomalies, seasonal_decompose


def build_timeseries_chart_data(
    timestamps: np.ndarray,
    values: np.ndarray,
    result: TrendResult,
) -> VisualizationData:
    """Build visualization data for a single variable's time-series chart.

    Includes the raw series, fitted trend line, anomalies, and
    decomposition components.

    Parameters
    ----------
    timestamps : np.ndarray
    values : np.ndarray
    result : TrendResult

    Returns
    -------
    VisualizationData
    """
    viz = VisualizationData()

    # Raw data
    viz.timestamps = timestamps.tolist()
    viz.values = [None if np.isnan(v) else float(v) for v in values]

    # Trend line (using Sen's slope + intercept)
    valid_mask = ~np.isnan(values)
    if np.any(valid_mask):
        slope_raw, intercept, _ = sens_slope(timestamps, values)
        viz.trend_line_x = timestamps.tolist()
        viz.trend_line_y = [float(intercept + slope_raw * t) for t in timestamps]

    # Anomalies
    try:
        anomalies, baseline = calculate_anomalies(values)
        viz.anomalies = [None if np.isnan(a) else float(a) for a in anomalies]
        viz.anomaly_baseline = baseline
    except Exception:
        pass

    # Confidence interval bands around the trend line
    if viz.trend_line_y:
        ci_half = abs(result.ci_upper - result.ci_lower) / 2
        viz.ci_upper_band = [y + ci_half * (t - timestamps[0])
                            for t, y in zip(timestamps, viz.trend_line_y)]
        viz.ci_lower_band = [y - ci_half * (t - timestamps[0])
                            for t, y in zip(timestamps, viz.trend_line_y)]

    # Seasonal decomposition (if enough data)
    try:
        trend_comp, seasonal_comp, resid_comp = seasonal_decompose(values)
        viz.trend_component = [None if np.isnan(v) else float(v) for v in trend_comp]
        viz.seasonal_component = [float(v) for v in seasonal_comp]
        viz.residual_component = [None if np.isnan(v) else float(v) for v in resid_comp]
    except Exception:
        pass

    return viz


def build_regional_comparison_data(
    results: List[TrendResult],
) -> VisualizationData:
    """Build visualization data for comparing trends across regions.

    Parameters
    ----------
    results : list of TrendResult

    Returns
    -------
    VisualizationData
    """
    viz = VisualizationData()
    viz.region_labels = [r.dataset for r in results]
    viz.region_slopes = [r.sens_slope for r in results]
    viz.region_p_values = [r.p_value for r in results]
    return viz


def build_geographic_map_data(
    lats: np.ndarray,
    lons: np.ndarray,
    slopes: np.ndarray,
    p_values: np.ndarray,
    alpha: float = 0.05,
) -> VisualizationData:
    """Build visualization data for a geographical trend map.

    Parameters
    ----------
    lats, lons : np.ndarray
        Grid cell coordinates.
    slopes : np.ndarray
        Sen's slope for each grid cell.
    p_values : np.ndarray
        p-value for each grid cell.
    alpha : float
        Significance threshold.

    Returns
    -------
    VisualizationData
    """
    viz = VisualizationData()
    viz.grid_lats = lats.tolist()
    viz.grid_lons = lons.tolist()
    viz.grid_slopes = slopes.tolist()
    viz.grid_significant = (p_values < alpha).tolist()
    return viz
