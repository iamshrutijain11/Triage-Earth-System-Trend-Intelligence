"""
TrendAnalyzer: the main orchestrator for trend analysis.

Integrates all submodules into a single, clean analysis pipeline.
Automatically selects the correct statistical test based on data
characteristics (seasonal vs non-seasonal, autocorrelated vs not).
"""

from __future__ import annotations

import numpy as np
from typing import Optional, Literal

from trend_engine.models import TrendResult, VisualizationData
from trend_engine.timeseries import build_timeseries, calculate_missing_data_stats
from trend_engine.decomposition import seasonal_decompose, calculate_anomalies
from trend_engine.trends import sens_slope, sens_slope_confidence_interval, linear_trend
from trend_engine.significance import (
    mann_kendall,
    seasonal_mann_kendall,
    mann_kendall_corrected,
    lag1_autocorrelation,
    is_autocorrelation_significant,
)
from trend_engine.confidence import slope_confidence_interval
from trend_engine.classification import (
    classify_trend,
    interpret_result,
    describe_methodology,
    describe_limitations,
)
from trend_engine.visualization import build_timeseries_chart_data


class TrendAnalyzer:
    """Statistically rigorous Earth-science trend analyzer.

    Usage
    -----
    >>> analyzer = TrendAnalyzer()
    >>> result = analyzer.analyze(
    ...     timestamps=time_array,
    ...     values=value_array,
    ...     variable_name="Surface Temperature",
    ...     dataset="GISTEMP v4",
    ...     unit="°C",
    ...     is_seasonal=True,
    ...     period=12,
    ...     slope_per="decade",
    ... )
    >>> print(result.to_json())
    """

    def __init__(self, alpha: float = 0.05, ci_level: float = 0.95):
        """
        Parameters
        ----------
        alpha : float
            Default significance threshold.
        ci_level : float
            Default confidence interval level.
        """
        self.alpha = float(alpha)
        self.ci_level = float(ci_level)

    def analyze(
        self,
        timestamps: np.ndarray,
        values: np.ndarray,
        variable_name: str,
        dataset: str,
        unit: str,
        is_seasonal: bool = False,
        period: int = 12,
        slope_per: str = "year",
        observation_period: Optional[str] = None,
    ) -> TrendResult:
        """Run the full trend analysis pipeline.

        Parameters
        ----------
        timestamps : np.ndarray
            Observation times (numeric; monotonically increasing).
        values : np.ndarray
            Observed values (NaN for missing).
        variable_name : str
            Name of the variable (e.g. "Precipitation").
        dataset : str
            Data source (e.g. "CHIRPS v2.0").
        unit : str
            Measurement unit (e.g. "mm", "°C").
        is_seasonal : bool
            Whether the data has a seasonal cycle. If True, the
            Seasonal Mann-Kendall test is used instead of standard MK.
        period : int
            Number of observations per season (12 for monthly).
        slope_per : str
            Desired slope time unit: "year", "decade", "month", "step".
        observation_period : str, optional
            Human-readable period string. Auto-generated if None.

        Returns
        -------
        TrendResult
        """
        timestamps = np.asarray(timestamps, dtype=float)
        values = np.asarray(values, dtype=float)

        # --- Step 1: Time-series & missing data ---
        _, _, missing_pct = build_timeseries(timestamps, values)
        n_obs = int(np.sum(~np.isnan(values)))

        if observation_period is None:
            t_valid = timestamps[~np.isnan(values)]
            if len(t_valid) > 0:
                observation_period = f"index {int(t_valid[0])} to {int(t_valid[-1])}"
            else:
                observation_period = "N/A"

        # --- Step 2: Compute time_unit_per_step ---
        time_unit_per_step = self._get_time_unit(
            slope_per, is_seasonal, period
        )
        slope_unit = f"{unit} / {slope_per}"

        # --- Step 3: Sen's slope ---
        slope, intercept, n_pairs = sens_slope(
            timestamps, values, time_unit_per_step=time_unit_per_step
        )
        raw_slope, _, _ = sens_slope(timestamps, values, time_unit_per_step=1.0)

        # --- Step 4: Confidence interval ---
        ci_lower, ci_upper = sens_slope_confidence_interval(
            timestamps, values,
            alpha=1 - self.ci_level,
            time_unit_per_step=time_unit_per_step,
        )

        # --- Step 5: Autocorrelation check (on detrended series) ---
        ac_significant, r1 = is_autocorrelation_significant(
            values=values,
            alpha=self.alpha,
            detrend_slope=raw_slope,
            timestamps=timestamps,
        )

        # --- Step 6: Significance test ---
        correction_factor = 1.0

        if is_seasonal:
            # Seasonal Mann-Kendall — the correct test for seasonal data
            S, z, p_value, significant = seasonal_mann_kendall(
                values, period=period, alpha=self.alpha
            )
            method_name = "Seasonal Mann-Kendall"
        elif ac_significant:
            # Standard MK with autocorrelation correction
            S, z, p_value, significant, correction_factor = mann_kendall_corrected(
                values=values,
                timestamps=timestamps,
                slope=raw_slope,
                alpha=self.alpha,
            )
            method_name = "Mann-Kendall (autocorrelation-corrected)"
        else:
            # Standard Mann-Kendall
            S, z, p_value, significant = mann_kendall(
                values, alpha=self.alpha
            )
            method_name = "Mann-Kendall"

        # --- Step 7: Classification ---
        direction = classify_trend(slope, p_value, self.alpha)

        # --- Step 8: Methodology description ---
        method_desc = describe_methodology(
            is_seasonal=is_seasonal,
            has_autocorrelation=ac_significant,
        )
        limitations = describe_limitations(
            missing_pct=missing_pct,
            n_obs=n_obs,
            is_seasonal=is_seasonal,
            has_autocorrelation=ac_significant,
        )

        return TrendResult(
            variable_name=variable_name,
            dataset=dataset,
            unit=unit,
            observation_count=n_obs,
            observation_period=observation_period,
            missing_data_pct=round(float(missing_pct), 2),
            trend_direction=direction,
            sens_slope=round(float(slope), 8),
            slope_unit=slope_unit,
            mk_statistic=round(float(S), 2),
            mk_z=round(float(z), 4),
            p_value=round(float(p_value), 6),
            significance_threshold=float(self.alpha),
            is_statistically_significant=bool(significant),
            ci_lower=round(float(ci_lower), 8),
            ci_upper=round(float(ci_upper), 8),
            ci_level=float(self.ci_level),
            analysis_method=method_desc,
            methodological_limitations=limitations,
            autocorrelation_lag1=round(float(r1), 4),
            autocorrelation_significant=bool(ac_significant),
            variance_correction_factor=(
                round(float(correction_factor), 4) if correction_factor != 1.0 else None
            ),
        )

    def analyze_with_visualization(
        self,
        timestamps: np.ndarray,
        values: np.ndarray,
        variable_name: str,
        dataset: str,
        unit: str,
        **kwargs,
    ) -> tuple:
        """Analyze and also return visualization data.

        Returns
        -------
        (TrendResult, VisualizationData)
        """
        result = self.analyze(
            timestamps, values, variable_name, dataset, unit, **kwargs
        )
        viz = build_timeseries_chart_data(timestamps, values, result)
        return result, viz

    @staticmethod
    def _get_time_unit(
        slope_per: str,
        is_seasonal: bool,
        period: int,
    ) -> float:
        """Convert slope_per to time_unit_per_step.

        If timestamps are simple indices (0, 1, 2, ...) and the data
        is monthly (period=12):
          - "year" -> 1 step = 1/12 year -> time_unit_per_step = 1/12
          - "decade" -> 1 step = 1/120 decade -> time_unit_per_step = 1/120
          - "step" -> 1.0

        For annual data (period=1 or not seasonal):
          - "year" -> 1.0
          - "decade" -> 0.1
        """
        if slope_per == "step":
            return 1.0

        if is_seasonal and period > 1:
            steps_per_year = period
        else:
            steps_per_year = 1

        if slope_per == "year":
            return 1.0 / steps_per_year
        elif slope_per == "decade":
            return 1.0 / (steps_per_year * 10)
        elif slope_per == "month":
            return 1.0
        else:
            return 1.0
