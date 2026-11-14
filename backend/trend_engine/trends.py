"""
Trend estimation: Sen's slope and linear regression.

Implements Theil-Sen median slope estimation with correct time-unit
handling, and OLS linear trend for comparison.
"""

from __future__ import annotations

import numpy as np
from itertools import combinations
from typing import Tuple, Optional

from trend_engine.timeseries import dropna_paired


def sens_slope(
    timestamps: np.ndarray,
    values: np.ndarray,
    time_unit_per_step: float = 1.0,
) -> Tuple[float, float, float]:
    """Theil-Sen median slope estimator.

    Parameters
    ----------
    timestamps : np.ndarray
        Observation times (numeric; e.g. fractional years, or indices).
    values : np.ndarray
        Observed values.
    time_unit_per_step : float
        Conversion factor from raw timestamp difference to desired
        reporting unit. For example, if timestamps are monthly indices
        and you want slope per decade, set this to 1/(12*10) = 1/120.
        Default 1.0 = slope per timestamp unit.

    Returns
    -------
    slope : float
        Sen's slope in reporting units.
    intercept : float
        Median intercept (Conover, 1999).
    n_pairs : float
        Number of valid pairs used.

    Notes
    -----
    Sen's slope is the median of all pairwise slopes:
        Q_ij = (y_j - y_i) / (t_j - t_i)   for all i < j
    """
    t, y = dropna_paired(timestamps, values)
    n = len(t)

    if n < 2:
        return 0.0, 0.0, 0.0

    # Compute all pairwise slopes
    slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            dt = t[j] - t[i]
            if dt != 0:
                slopes.append((y[j] - y[i]) / dt)

    if len(slopes) == 0:
        return 0.0, float(np.median(y)), 0.0

    slope_raw = float(np.median(slopes))
    slope = slope_raw / time_unit_per_step if time_unit_per_step != 1.0 else slope_raw

    # Intercept: median of (y_i - slope_raw * t_i)
    intercept = float(np.median(y - slope_raw * t))

    return slope, intercept, float(len(slopes))


def sens_slope_confidence_interval(
    timestamps: np.ndarray,
    values: np.ndarray,
    alpha: float = 0.05,
    time_unit_per_step: float = 1.0,
) -> Tuple[float, float]:
    """Confidence interval for Sen's slope.

    Uses the distribution of pairwise slopes and the normal approximation
    for the rank of the CI bounds (Hollander & Wolfe, 1999).

    Parameters
    ----------
    timestamps, values : np.ndarray
    alpha : float
        Significance level (default 0.05 for 95% CI).
    time_unit_per_step : float
        Same as in sens_slope.

    Returns
    -------
    ci_lower, ci_upper : float
        Lower and upper confidence bounds for the slope.
    """
    from scipy import stats

    t, y = dropna_paired(timestamps, values)
    n = len(t)

    if n < 3:
        s, _, _ = sens_slope(timestamps, values, time_unit_per_step)
        return s, s

    # All pairwise slopes
    all_slopes = []
    for i in range(n):
        for j in range(i + 1, n):
            dt = t[j] - t[i]
            if dt != 0:
                all_slopes.append((y[j] - y[i]) / dt)

    all_slopes = np.sort(all_slopes)
    N = len(all_slopes)

    if N == 0:
        return 0.0, 0.0

    # Confidence interval rank bounds
    z = stats.norm.ppf(1 - alpha / 2)
    C_alpha = z * np.sqrt(n * (n - 1) * (2 * n + 5) / 18.0)

    # Lower and upper rank (1-based → 0-based)
    M1 = int(np.round((N - C_alpha) / 2.0))
    M2 = int(np.round((N + C_alpha) / 2.0))

    M1 = max(0, min(M1, N - 1))
    M2 = max(0, min(M2, N - 1))

    lo = all_slopes[M1]
    hi = all_slopes[M2]

    if time_unit_per_step != 1.0:
        lo /= time_unit_per_step
        hi /= time_unit_per_step

    return float(lo), float(hi)


def linear_trend(
    timestamps: np.ndarray,
    values: np.ndarray,
) -> Tuple[float, float, float]:
    """Ordinary least squares linear trend.

    Parameters
    ----------
    timestamps, values : np.ndarray

    Returns
    -------
    slope : float
    intercept : float
    r_squared : float
    """
    t, y = dropna_paired(timestamps, values)
    n = len(t)

    if n < 2:
        return 0.0, 0.0, 0.0

    t_mean = np.mean(t)
    y_mean = np.mean(y)
    ss_tt = np.sum((t - t_mean) ** 2)
    ss_ty = np.sum((t - t_mean) * (y - y_mean))
    ss_yy = np.sum((y - y_mean) ** 2)

    if ss_tt == 0:
        return 0.0, float(y_mean), 0.0

    slope = ss_ty / ss_tt
    intercept = y_mean - slope * t_mean
    r_squared = (ss_ty ** 2) / (ss_tt * ss_yy) if ss_yy > 0 else 0.0

    return float(slope), float(intercept), float(r_squared)
