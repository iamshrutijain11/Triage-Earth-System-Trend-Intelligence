"""
Seasonal decomposition and anomaly calculation.

Implements additive seasonal decomposition using centered moving
averages and anomaly computation relative to a climatological baseline.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Optional


def seasonal_decompose(
    values: np.ndarray,
    period: int = 12,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Classical additive seasonal decomposition via moving averages.

    Parameters
    ----------
    values : np.ndarray
        Time series values (may contain NaN).
    period : int
        Number of observations per season (12 for monthly data).

    Returns
    -------
    trend : np.ndarray
        Trend component (NaN-padded at edges).
    seasonal : np.ndarray
        Seasonal component (repeating pattern).
    residual : np.ndarray
        Residual = values - trend - seasonal.
    """
    n = len(values)
    if n < 2 * period:
        raise ValueError(
            f"Need at least {2 * period} observations for decomposition "
            f"with period={period}, got {n}."
        )

    # --- Step 1: Estimate trend via centered moving average ---
    trend = np.full(n, np.nan)
    half = period // 2

    if period % 2 == 0:
        # Even period: 2×moving-average for centering
        for i in range(half, n - half):
            window = values[i - half: i + half + 1]
            if not np.any(np.isnan(window)):
                # Weight endpoints by 0.5 for centering
                trend[i] = (
                    0.5 * window[0] + np.sum(window[1:-1]) + 0.5 * window[-1]
                ) / period
    else:
        for i in range(half, n - half):
            window = values[i - half: i + half + 1]
            if not np.any(np.isnan(window)):
                trend[i] = np.nanmean(window)

    # --- Step 2: Detrended series ---
    detrended = values - trend

    # --- Step 3: Seasonal component (average of each season position) ---
    seasonal_means = np.zeros(period)
    for s in range(period):
        season_vals = detrended[s::period]
        valid = season_vals[~np.isnan(season_vals)]
        seasonal_means[s] = np.mean(valid) if len(valid) > 0 else 0.0

    # Center seasonal component to sum to zero
    seasonal_means -= np.mean(seasonal_means)

    # Tile seasonal pattern across full length
    seasonal = np.tile(seasonal_means, n // period + 1)[:n]

    # --- Step 4: Residual ---
    residual = values - trend - seasonal

    return trend, seasonal, residual


def calculate_anomalies(
    values: np.ndarray,
    baseline_start: int = 0,
    baseline_end: Optional[int] = None,
    period: int = 12,
) -> Tuple[np.ndarray, float]:
    """Calculate anomalies relative to a climatological baseline.

    For monthly data, computes monthly means over the baseline period,
    then subtracts them to produce anomalies.

    Parameters
    ----------
    values : np.ndarray
        Full time series.
    baseline_start : int
        Index of baseline period start (inclusive).
    baseline_end : int or None
        Index of baseline period end (exclusive). None = full series.
    period : int
        Seasonal period (12 for monthly).

    Returns
    -------
    anomalies : np.ndarray
        Anomaly series.
    baseline_mean : float
        Overall baseline mean.
    """
    if baseline_end is None:
        baseline_end = len(values)

    baseline = values[baseline_start:baseline_end]
    n = len(values)

    # Compute monthly climatology from baseline
    clim = np.zeros(period)
    for s in range(period):
        season_vals = baseline[s::period]
        valid = season_vals[~np.isnan(season_vals)]
        clim[s] = np.mean(valid) if len(valid) > 0 else 0.0

    # Subtract climatology
    anomalies = np.full(n, np.nan)
    for i in range(n):
        if not np.isnan(values[i]):
            anomalies[i] = values[i] - clim[i % period]

    baseline_mean = float(np.nanmean(baseline))

    return anomalies, baseline_mean


def calculate_annual_anomalies(
    monthly_values: np.ndarray,
    baseline_start_year_idx: int = 0,
    baseline_end_year_idx: Optional[int] = None,
) -> Tuple[np.ndarray, float]:
    """Aggregate monthly data to annual means, then compute anomalies.

    Parameters
    ----------
    monthly_values : np.ndarray
        Monthly time series (length must be divisible by 12).
    baseline_start_year_idx : int
        Start year index for baseline.
    baseline_end_year_idx : int or None
        End year index for baseline.

    Returns
    -------
    annual_anomalies : np.ndarray
    baseline_annual_mean : float
    """
    n = len(monthly_values)
    n_years = n // 12
    remainder = n % 12
    if remainder > 0:
        # Truncate incomplete final year
        monthly_values = monthly_values[: n_years * 12]

    annual_means = np.array([
        np.nanmean(monthly_values[y * 12: (y + 1) * 12])
        for y in range(n_years)
    ])

    if baseline_end_year_idx is None:
        baseline_end_year_idx = n_years

    baseline = annual_means[baseline_start_year_idx:baseline_end_year_idx]
    baseline_mean = float(np.nanmean(baseline))

    anomalies = annual_means - baseline_mean

    return anomalies, baseline_mean
