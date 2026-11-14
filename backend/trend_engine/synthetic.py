"""
Synthetic test dataset generator for scientific validation.

Provides 7 canonical benchmark time series with mathematically known
ground-truth properties:
1. Clearly increasing trend
2. Clearly decreasing trend
3. Stationary series
4. Seasonal series without a long-term trend
5. Seasonal series with an underlying trend
6. Series with missing observations
7. Series with serial autocorrelation

Used to rigorously verify that the statistical engine handles all cases correctly.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, Tuple, Any


def generate_synthetic_datasets(seed: int = 42) -> Dict[str, Dict[str, Any]]:
    """Generate all 7 canonical synthetic datasets.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    dict
        Mapping of test case key to dictionary with keys:
        - "timestamps": np.ndarray
        - "values": np.ndarray
        - "true_slope": float
        - "expected_direction": str ("increasing", "decreasing", "no trend")
        - "is_seasonal": bool
        - "period": int
        - "has_autocorrelation": bool
        - "has_missing": bool
        - "description": str
    """
    rng = np.random.default_rng(seed)
    datasets: Dict[str, Dict[str, Any]] = {}

    # Case 1: Clearly increasing trend
    n1 = 120
    t1 = np.arange(n1, dtype=float)
    slope1 = 0.08
    noise1 = rng.normal(0, 0.5, size=n1)
    y1 = 10.0 + slope1 * t1 + noise1
    datasets["increasing"] = {
        "timestamps": t1,
        "values": y1,
        "true_slope": slope1,
        "expected_direction": "increasing",
        "is_seasonal": False,
        "period": 1,
        "has_autocorrelation": False,
        "has_missing": False,
        "description": "Linear increasing trend with additive Gaussian noise",
    }

    # Case 2: Clearly decreasing trend
    n2 = 120
    t2 = np.arange(n2, dtype=float)
    slope2 = -0.07
    noise2 = rng.normal(0, 0.5, size=n2)
    y2 = 50.0 + slope2 * t2 + noise2
    datasets["decreasing"] = {
        "timestamps": t2,
        "values": y2,
        "true_slope": slope2,
        "expected_direction": "decreasing",
        "is_seasonal": False,
        "period": 1,
        "has_autocorrelation": False,
        "has_missing": False,
        "description": "Linear decreasing trend with additive Gaussian noise",
    }

    # Case 3: Stationary series
    n3 = 120
    t3 = np.arange(n3, dtype=float)
    noise3 = rng.normal(0, 1.0, size=n3)
    y3 = 25.0 + noise3
    datasets["stationary"] = {
        "timestamps": t3,
        "values": y3,
        "true_slope": 0.0,
        "expected_direction": "no trend",
        "is_seasonal": False,
        "period": 1,
        "has_autocorrelation": False,
        "has_missing": False,
        "description": "White noise stationary series around constant mean",
    }

    # Case 4: Seasonal series without a long-term trend
    # 10 years of monthly data (120 observations)
    n4 = 120
    t4 = np.arange(n4, dtype=float)
    seasonal_pattern = 15.0 * np.sin(2 * np.pi * t4 / 12.0)
    noise4 = rng.normal(0, 1.2, size=n4)
    y4 = 20.0 + seasonal_pattern + noise4
    datasets["seasonal_no_trend"] = {
        "timestamps": t4,
        "values": y4,
        "true_slope": 0.0,
        "expected_direction": "no trend",
        "is_seasonal": True,
        "period": 12,
        "has_autocorrelation": False,
        "has_missing": False,
        "description": "Pure seasonal cycle (period=12) with zero long-term trend",
    }

    # Case 5: Seasonal series with underlying trend
    # 10 years of monthly data (120 observations) + 0.05/month upward trend
    n5 = 120
    t5 = np.arange(n5, dtype=float)
    slope5 = 0.05
    noise5 = rng.normal(0, 1.0, size=n5)
    y5 = 15.0 + slope5 * t5 + 10.0 * np.sin(2 * np.pi * t5 / 12.0) + noise5
    datasets["seasonal_with_trend"] = {
        "timestamps": t5,
        "values": y5,
        "true_slope": slope5,
        "expected_direction": "increasing",
        "is_seasonal": True,
        "period": 12,
        "has_autocorrelation": False,
        "has_missing": False,
        "description": "Seasonal cycle (period=12) with superimposed positive linear trend",
    }

    # Case 6: Series with missing observations (20% missing, increasing trend)
    n6 = 120
    t6 = np.arange(n6, dtype=float)
    slope6 = 0.06
    noise6 = rng.normal(0, 0.6, size=n6)
    y6 = 5.0 + slope6 * t6 + noise6
    missing_indices = rng.choice(n6, size=int(0.20 * n6), replace=False)
    y6_missing = y6.copy()
    y6_missing[missing_indices] = np.nan
    datasets["missing_data"] = {
        "timestamps": t6,
        "values": y6_missing,
        "true_slope": slope6,
        "expected_direction": "increasing",
        "is_seasonal": False,
        "period": 1,
        "has_autocorrelation": False,
        "has_missing": True,
        "missing_indices": missing_indices,
        "description": "Increasing trend with 20% random missing observations (NaN)",
    }

    # Case 7: Series with serial autocorrelation (AR(1) process with phi=0.6)
    n7 = 150
    t7 = np.arange(n7, dtype=float)
    phi = 0.6
    ar_noise = rng.normal(0, 1.0, size=n7)
    ar_series = np.zeros(n7)
    for i in range(1, n7):
        ar_series[i] = phi * ar_series[i - 1] + ar_noise[i]

    # No underlying trend in this AR(1) series
    y7 = 30.0 + ar_series
    datasets["autocorrelated"] = {
        "timestamps": t7,
        "values": y7,
        "true_slope": 0.0,
        "expected_direction": "no trend",
        "is_seasonal": False,
        "period": 1,
        "has_autocorrelation": True,
        "ar_phi": phi,
        "has_missing": False,
        "description": "Stationary AR(1) process with significant serial autocorrelation (phi=0.6)",
    }

    return datasets
