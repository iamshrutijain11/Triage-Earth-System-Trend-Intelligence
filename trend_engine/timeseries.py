"""
Time-series generation and missing-data analysis.

Handles construction of clean time series from raw observations,
gap detection, interpolation tracking, and completeness reporting.
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Tuple


def build_timeseries(
    timestamps: np.ndarray,
    values: np.ndarray,
    expected_freq: Optional[str] = None,
) -> Tuple[np.ndarray, np.ndarray, float]:
    """Build a clean time series and report missing-data statistics.

    Parameters
    ----------
    timestamps : array-like
        Observation times (numeric or datetime-ordinal).
    values : array-like
        Observed values; NaN indicates missing.
    expected_freq : str, optional
        Expected observation frequency for gap analysis
        ("monthly", "daily", "annual").

    Returns
    -------
    timestamps : np.ndarray
        Cleaned timestamps (same length, NaN-indexed entries kept for
        positional alignment).
    values : np.ndarray
        Cleaned values with NaNs preserved (no interpolation —
        the statistical tests handle NaN-aware computation).
    missing_pct : float
        Percentage of missing (NaN) observations (0–100).
    """
    timestamps = np.asarray(timestamps, dtype=float)
    values = np.asarray(values, dtype=float)

    if len(timestamps) != len(values):
        raise ValueError(
            f"Timestamp ({len(timestamps)}) and value ({len(values)}) "
            "arrays must have the same length."
        )

    n_total = len(values)
    n_missing = int(np.sum(np.isnan(values)))
    missing_pct = (n_missing / n_total * 100.0) if n_total > 0 else 0.0

    return timestamps, values, missing_pct


def calculate_missing_data_stats(values: np.ndarray) -> dict:
    """Detailed missing-data diagnostics.

    Returns
    -------
    dict with keys:
        total, missing, valid, missing_pct,
        max_consecutive_gap, gap_positions
    """
    values = np.asarray(values, dtype=float)
    is_nan = np.isnan(values)
    n_total = len(values)
    n_missing = int(np.sum(is_nan))
    n_valid = n_total - n_missing

    # Find consecutive gaps
    max_gap = 0
    current_gap = 0
    gap_starts = []
    for i, m in enumerate(is_nan):
        if m:
            if current_gap == 0:
                gap_starts.append(i)
            current_gap += 1
            max_gap = max(max_gap, current_gap)
        else:
            current_gap = 0

    return {
        "total": n_total,
        "missing": n_missing,
        "valid": n_valid,
        "missing_pct": (n_missing / n_total * 100.0) if n_total > 0 else 0.0,
        "max_consecutive_gap": max_gap,
        "gap_positions": gap_starts,
    }


def dropna_paired(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Drop entries where either x or y is NaN, preserving pairing."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    return x[mask], y[mask]
