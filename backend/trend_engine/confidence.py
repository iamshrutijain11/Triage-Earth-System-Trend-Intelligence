"""
Confidence interval calculation and multiple hypothesis testing correction.

Provides:
- Sen's slope CI (delegated to trends module)
- Benjamini-Hochberg FDR correction for spatial grid-cell testing
- Bonferroni correction
"""

from __future__ import annotations

import numpy as np
from typing import List, Tuple

from trend_engine.trends import sens_slope_confidence_interval


def slope_confidence_interval(
    timestamps: np.ndarray,
    values: np.ndarray,
    alpha: float = 0.05,
    time_unit_per_step: float = 1.0,
) -> Tuple[float, float]:
    """Wrapper: 95% CI for Sen's slope.

    Parameters
    ----------
    timestamps, values : np.ndarray
    alpha : float
    time_unit_per_step : float

    Returns
    -------
    ci_lower, ci_upper : float
    """
    return sens_slope_confidence_interval(
        timestamps, values, alpha=alpha, time_unit_per_step=time_unit_per_step
    )


def benjamini_hochberg(
    p_values: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """Benjamini-Hochberg False Discovery Rate correction.

    For spatial grid-cell testing — controls the expected fraction
    of false positives among rejected hypotheses.

    Parameters
    ----------
    p_values : array-like
        Raw p-values from multiple tests.
    alpha : float
        Desired FDR level.

    Returns
    -------
    adjusted_p : np.ndarray
        BH-adjusted p-values.
    significant : np.ndarray
        Boolean array indicating which tests remain significant.
    """
    p = np.asarray(p_values, dtype=float)
    m = len(p)

    if m == 0:
        return np.array([]), np.array([], dtype=bool)

    # Sort p-values
    sorted_idx = np.argsort(p)
    sorted_p = p[sorted_idx]

    # BH adjusted p-values
    adjusted = np.zeros(m)
    for i in range(m - 1, -1, -1):
        rank = i + 1
        if i == m - 1:
            adjusted[i] = sorted_p[i]
        else:
            adjusted[i] = min(adjusted[i + 1], sorted_p[i] * m / rank)

    # Unsort
    result = np.zeros(m)
    result[sorted_idx] = adjusted

    significant = result < alpha

    return result, significant


def bonferroni(
    p_values: np.ndarray,
    alpha: float = 0.05,
) -> Tuple[np.ndarray, np.ndarray]:
    """Bonferroni correction for multiple hypothesis testing.

    More conservative than BH — controls the family-wise error rate.

    Parameters
    ----------
    p_values : array-like
    alpha : float

    Returns
    -------
    adjusted_p : np.ndarray
    significant : np.ndarray (bool)
    """
    p = np.asarray(p_values, dtype=float)
    m = len(p)

    if m == 0:
        return np.array([]), np.array([], dtype=bool)

    adjusted = np.minimum(p * m, 1.0)
    significant = adjusted < alpha

    return adjusted, significant
