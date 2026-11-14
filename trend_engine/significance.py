"""
Statistical significance testing.

Implements:
- Standard Mann-Kendall test (Mann 1945, Kendall 1975)
- Seasonal Mann-Kendall test (Hirsch et al. 1982)
- Serial autocorrelation detection on detrended residuals
- Hamed & Rao (1998) modified variance for autocorrelated data
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Optional


def _sign(x: float) -> int:
    """Sign function: returns -1, 0, or +1."""
    if x > 0:
        return 1
    elif x < 0:
        return -1
    return 0


def mann_kendall(
    values: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[float, float, float, bool]:
    """Standard Mann-Kendall trend test.

    Parameters
    ----------
    values : np.ndarray
        Time series values (NaN entries are dropped).
    alpha : float
        Significance threshold.

    Returns
    -------
    S : float
        Mann-Kendall S statistic.
    z : float
        Normalized Z statistic.
    p_value : float
        Two-sided p-value.
    significant : bool
        Whether p < alpha.
    """
    from scipy import stats

    y = values[~np.isnan(values)]
    n = len(y)

    if n < 3:
        return 0.0, 0.0, 1.0, False

    # S statistic
    S = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            S += _sign(y[j] - y[i])

    # Tied groups correction
    unique, counts = np.unique(y, return_counts=True)
    tied_groups = counts[counts > 1]

    var_S = n * (n - 1) * (2 * n + 5)
    for t_p in tied_groups:
        var_S -= t_p * (t_p - 1) * (2 * t_p + 5)
    var_S /= 18.0

    if var_S <= 0:
        return float(S), 0.0, 1.0, False

    # Z statistic (continuity correction)
    if S > 0:
        z = (S - 1) / np.sqrt(var_S)
    elif S < 0:
        z = (S + 1) / np.sqrt(var_S)
    else:
        z = 0.0

    p_value = 2.0 * (1.0 - stats.norm.cdf(abs(z)))

    return float(S), float(z), float(p_value), bool(p_value < alpha)


def lag1_autocorrelation(values: np.ndarray) -> float:
    """Compute lag-1 autocorrelation coefficient.

    Parameters
    ----------
    values : np.ndarray
        Time series (NaNs are dropped).

    Returns
    -------
    r1 : float
        Lag-1 autocorrelation.
    """
    y = values[~np.isnan(values)]
    n = len(y)
    if n < 3:
        return 0.0

    y_mean = np.mean(y)
    numerator = np.sum((y[:-1] - y_mean) * (y[1:] - y_mean))
    denominator = np.sum((y - y_mean) ** 2)

    if denominator == 0:
        return 0.0

    return float(numerator / denominator)


def is_autocorrelation_significant(
    values: np.ndarray,
    alpha: float = 0.05,
    detrend_slope: Optional[float] = None,
    timestamps: Optional[np.ndarray] = None,
) -> Tuple[bool, float]:
    """Test whether lag-1 autocorrelation is statistically significant.

    If detrend_slope is provided, autocorrelation is evaluated on the
    residuals (detrended series), following standard climatology practice
    (Hamed & Rao 1998, Yue et al. 2002).

    Parameters
    ----------
    values : np.ndarray
    alpha : float
    detrend_slope : float, optional
    timestamps : np.ndarray, optional

    Returns
    -------
    significant : bool
    r1 : float
    """
    valid_mask = ~np.isnan(values)
    y = values[valid_mask]
    n = len(y)

    if n < 10:
        return False, 0.0

    if detrend_slope is not None and timestamps is not None:
        t = timestamps[valid_mask]
        residuals = y - detrend_slope * t
    else:
        residuals = y

    r1 = lag1_autocorrelation(residuals)

    from scipy import stats
    z_crit = stats.norm.ppf(1 - alpha / 2)
    bound = z_crit / np.sqrt(n)

    return bool(abs(r1) > bound), float(r1)


def mann_kendall_corrected(
    values: np.ndarray,
    timestamps: Optional[np.ndarray] = None,
    slope: Optional[float] = None,
    alpha: float = 0.05,
) -> Tuple[float, float, float, bool, float]:
    """Mann-Kendall test with Hamed & Rao (1998) variance correction
    for serial autocorrelation.

    Ranks are computed on the detrended series so that an existing trend
    does not artificially inflate serial autocorrelation.

    Parameters
    ----------
    values : np.ndarray
    timestamps : np.ndarray, optional
    slope : float, optional
        Pre-calculated Sen's slope for detrending.
    alpha : float

    Returns
    -------
    S, z, p_value, significant, correction_factor
    """
    from scipy import stats

    valid_mask = ~np.isnan(values)
    y = values[valid_mask]
    n = len(y)

    if n < 3:
        return 0.0, 0.0, 1.0, False, 1.0

    if timestamps is not None:
        t = timestamps[valid_mask]
    else:
        t = np.arange(n, dtype=float)

    # Standard S statistic on original observations
    S = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            S += _sign(y[j] - y[i])

    # Standard variance
    unique, counts = np.unique(y, return_counts=True)
    tied_groups = counts[counts > 1]

    var_S = n * (n - 1) * (2 * n + 5)
    for t_p in tied_groups:
        var_S -= t_p * (t_p - 1) * (2 * t_p + 5)
    var_S /= 18.0

    # Detrend data before computing rank autocorrelation
    if slope is None:
        from trend_engine.trends import sens_slope
        slope, _, _ = sens_slope(t, y)

    residuals = y - slope * t
    ranks = stats.rankdata(residuals)
    rank_mean = (n + 1) / 2.0
    rank_var = np.sum((ranks - rank_mean) ** 2)

    # Critical bound for significant autocorrelation at lag k
    z_crit = stats.norm.ppf(1 - alpha / 2)
    sig_bound = z_crit / np.sqrt(n)

    correction_factor = 1.0
    if rank_var > 0 and n >= 10:
        n_s = 0.0
        max_lag = min(n - 2, 30)  # Standard practice: limit lag to n/4 or 30
        for lag in range(1, max_lag + 1):
            num = np.sum((ranks[:-lag] - rank_mean) * (ranks[lag:] - rank_mean))
            r_lag = num / rank_var
            # Only sum lags where autocorrelation is statistically significant
            if abs(r_lag) > sig_bound:
                n_s += (n - lag) * r_lag

        correction_factor = 1.0 + (2.0 / n) * n_s
        correction_factor = max(float(correction_factor), 1.0)
        var_S *= correction_factor

    if var_S <= 0:
        return float(S), 0.0, 1.0, False, float(correction_factor)

    if S > 0:
        z = (S - 1) / np.sqrt(var_S)
    elif S < 0:
        z = (S + 1) / np.sqrt(var_S)
    else:
        z = 0.0

    p_value = 2.0 * (1.0 - stats.norm.cdf(abs(z)))

    return float(S), float(z), float(p_value), bool(p_value < alpha), float(correction_factor)


def seasonal_mann_kendall(
    values: np.ndarray,
    period: int = 12,
    alpha: float = 0.05,
) -> Tuple[float, float, float, bool]:
    """Seasonal Mann-Kendall test (Hirsch et al., 1982).

    Computes the Mann-Kendall S statistic separately for each season
    (e.g. each calendar month), then sums them.

    Parameters
    ----------
    values : np.ndarray
    period : int
    alpha : float

    Returns
    -------
    S_total : float
    z : float
    p_value : float
    significant : bool
    """
    from scipy import stats

    n = len(values)
    S_total = 0.0
    var_total = 0.0

    for s in range(period):
        season_vals = values[s::period]
        y_s = season_vals[~np.isnan(season_vals)]
        n_s = len(y_s)

        if n_s < 2:
            continue

        S_s = 0.0
        for i in range(n_s):
            for j in range(i + 1, n_s):
                S_s += _sign(y_s[j] - y_s[i])

        S_total += S_s

        unique, counts = np.unique(y_s, return_counts=True)
        tied = counts[counts > 1]

        var_s = n_s * (n_s - 1) * (2 * n_s + 5)
        for t_p in tied:
            var_s -= t_p * (t_p - 1) * (2 * t_p + 5)
        var_s /= 18.0

        var_total += var_s

    if var_total <= 0:
        return float(S_total), 0.0, 1.0, False

    if S_total > 0:
        z = (S_total - 1) / np.sqrt(var_total)
    elif S_total < 0:
        z = (S_total + 1) / np.sqrt(var_total)
    else:
        z = 0.0

    p_value = 2.0 * (1.0 - stats.norm.cdf(abs(z)))

    return float(S_total), float(z), float(p_value), bool(p_value < alpha)
