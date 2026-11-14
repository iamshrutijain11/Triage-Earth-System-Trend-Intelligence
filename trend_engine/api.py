"""
Clean API endpoints for trend analysis and regional comparison.

These functions provide the public interface for the trend engine,
independent of any frontend or AI model.
"""

from __future__ import annotations

import numpy as np
from typing import List, Optional, Dict, Any

from trend_engine.models import TrendResult, VisualizationData
from trend_engine.analyzer import TrendAnalyzer
from trend_engine.confidence import benjamini_hochberg, bonferroni
from trend_engine.visualization import (
    build_timeseries_chart_data,
    build_regional_comparison_data,
    build_geographic_map_data,
)


def analyze_variable(
    timestamps: np.ndarray,
    values: np.ndarray,
    variable_name: str,
    dataset: str,
    unit: str,
    is_seasonal: bool = False,
    period: int = 12,
    slope_per: str = "year",
    alpha: float = 0.05,
    observation_period: Optional[str] = None,
    include_visualization: bool = False,
) -> Dict[str, Any]:
    """Analyze a single variable's time series.

    This is the primary API endpoint.

    Parameters
    ----------
    timestamps : array-like
    values : array-like
    variable_name : str
    dataset : str
    unit : str
    is_seasonal : bool
    period : int
    slope_per : str
    alpha : float
    observation_period : str, optional
    include_visualization : bool

    Returns
    -------
    dict with keys:
        "result" : TrendResult dict
        "interpretation" : str
        "visualization" : VisualizationData dict (if requested)
    """
    timestamps = np.asarray(timestamps, dtype=float)
    values = np.asarray(values, dtype=float)

    analyzer = TrendAnalyzer(alpha=alpha)
    result = analyzer.analyze(
        timestamps=timestamps,
        values=values,
        variable_name=variable_name,
        dataset=dataset,
        unit=unit,
        is_seasonal=is_seasonal,
        period=period,
        slope_per=slope_per,
        observation_period=observation_period,
    )

    from trend_engine.classification import interpret_result

    interpretation = interpret_result(
        variable_name=result.variable_name,
        trend_direction=result.trend_direction,
        sens_slope=result.sens_slope,
        slope_unit=result.slope_unit,
        p_value=result.p_value,
        alpha=result.significance_threshold,
        ci_lower=result.ci_lower,
        ci_upper=result.ci_upper,
        missing_pct=result.missing_data_pct,
        autocorrelation_corrected=result.autocorrelation_significant or False,
    )

    output: Dict[str, Any] = {
        "result": result.to_dict(),
        "interpretation": interpretation,
    }

    if include_visualization:
        viz = build_timeseries_chart_data(timestamps, values, result)
        output["visualization"] = viz.to_dict()

    return output


def compare_regions(
    region_analyses: List[Dict[str, Any]],
    correction_method: str = "fdr",
) -> Dict[str, Any]:
    """Compare trend results across multiple regions.

    Applies multiple hypothesis testing correction when comparing
    several regions/grid cells.

    Parameters
    ----------
    region_analyses : list of dict
        Each dict must contain:
            - "timestamps": array-like
            - "values": array-like
            - "variable_name": str
            - "dataset": str (used as region label)
            - "unit": str
            - Additional kwargs for analyze_variable.
    correction_method : str
        "fdr" for Benjamini-Hochberg, "bonferroni" for Bonferroni.

    Returns
    -------
    dict with keys:
        "results" : list of TrendResult dicts
        "corrected_p_values" : list of float
        "corrected_significant" : list of bool
        "correction_method" : str
        "visualization" : VisualizationData dict (regional comparison)
    """
    results = []
    raw_p_values = []

    for region in region_analyses:
        analysis = analyze_variable(**region)
        result = analysis["result"]
        results.append(result)
        raw_p_values.append(result["p_value"])

    # Multiple testing correction
    p_arr = np.array(raw_p_values)
    if correction_method == "fdr":
        adj_p, adj_sig = benjamini_hochberg(p_arr)
    else:
        adj_p, adj_sig = bonferroni(p_arr)

    # Update results with corrected values
    for i, res in enumerate(results):
        res["adjusted_p_value"] = float(adj_p[i])
        res["multiple_testing_method"] = correction_method.upper()

    # Build TrendResult objects for visualization
    trend_results = []
    for res in results:
        tr = TrendResult(**{k: v for k, v in res.items() if k in TrendResult.__dataclass_fields__})
        trend_results.append(tr)

    viz = build_regional_comparison_data(trend_results)

    return {
        "results": results,
        "corrected_p_values": adj_p.tolist(),
        "corrected_significant": adj_sig.tolist(),
        "correction_method": correction_method.upper(),
        "visualization": viz.to_dict(),
    }


def analyze_spatial_grid(
    lats: np.ndarray,
    lons: np.ndarray,
    grid_timeseries: List[np.ndarray],
    timestamps: np.ndarray,
    variable_name: str,
    dataset: str,
    unit: str,
    is_seasonal: bool = False,
    period: int = 12,
    slope_per: str = "decade",
    alpha: float = 0.05,
    correction_method: str = "fdr",
) -> Dict[str, Any]:
    """Analyze trends across a spatial grid of time series.

    Applies multiple hypothesis testing correction across all grid cells.

    Parameters
    ----------
    lats, lons : np.ndarray
        1D arrays of grid cell coordinates.
    grid_timeseries : list of np.ndarray
        One time series per grid cell.
    timestamps : np.ndarray
    variable_name, dataset, unit : str
    is_seasonal : bool
    period : int
    slope_per : str
    alpha : float
    correction_method : str

    Returns
    -------
    dict with grid results, corrected p-values, and map visualization data.
    """
    analyzer = TrendAnalyzer(alpha=alpha)

    slopes = []
    p_values = []
    all_results = []

    for ts in grid_timeseries:
        result = analyzer.analyze(
            timestamps=timestamps,
            values=np.asarray(ts, dtype=float),
            variable_name=variable_name,
            dataset=dataset,
            unit=unit,
            is_seasonal=is_seasonal,
            period=period,
            slope_per=slope_per,
        )
        slopes.append(result.sens_slope)
        p_values.append(result.p_value)
        all_results.append(result.to_dict())

    # Multiple testing correction
    p_arr = np.array(p_values)
    if correction_method == "fdr":
        adj_p, adj_sig = benjamini_hochberg(p_arr, alpha)
    else:
        adj_p, adj_sig = bonferroni(p_arr, alpha)

    # Update results
    for i, res in enumerate(all_results):
        res["adjusted_p_value"] = float(adj_p[i])
        res["multiple_testing_method"] = correction_method.upper()

    # Map visualization
    viz = build_geographic_map_data(
        lats=np.asarray(lats),
        lons=np.asarray(lons),
        slopes=np.array(slopes),
        p_values=adj_p,
        alpha=alpha,
    )

    n_significant = int(np.sum(adj_sig))

    return {
        "results": all_results,
        "corrected_p_values": adj_p.tolist(),
        "corrected_significant": adj_sig.tolist(),
        "n_cells": len(grid_timeseries),
        "n_significant": n_significant,
        "correction_method": correction_method.upper(),
        "visualization": viz.to_dict(),
    }
