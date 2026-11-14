"""
Module B: Trend Laboratory.

Interactive time-series analysis laboratory featuring:
- Historical observation series plotting
- Theil-Sen median slope vs Ordinary Least Squares (OLS) trend line comparison
- Hollander-Wolfe non-parametric 95% confidence interval uncertainty bands
- Classical additive seasonal decomposition (Trend, Seasonality, Residuals)
- Climatological monthly anomaly charts relative to multi-decadal baseline
"""

from __future__ import annotations
import streamlit as st
import numpy as np
import pandas as pd

from trend_engine.models import TrendResult, VisualizationData
from trend_engine.decomposition import seasonal_decompose, calculate_anomalies
from trend_engine.trends import linear_trend


def render_trend_lab_view(
    series_data: dict,
    trend_result: TrendResult,
    viz_data: VisualizationData,
) -> None:
    """Render Module B: Trend Laboratory view."""
    st.markdown("## 📈 Module B: Trend Laboratory")
    st.markdown(
        "Analyze multi-decadal trajectory, separate recurring seasonal cycles, calculate "
        "climatological anomalies, and contrast robust Theil-Sen estimators against classical regression."
    )

    timestamps = np.array(series_data["timestamps"], dtype=float)
    values = np.array(series_data["values"], dtype=float)
    n_obs = len(values)

    # 1. Top KPI Metric Summary
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Observation Count", f"{n_obs} months", f"{timestamps[0]:.0f}–{timestamps[-1]:.0f}")
    kpi2.metric(
        "Sen's Slope",
        f"{trend_result.sens_slope:+.4f} {trend_result.slope_unit}",
        trend_result.trend_direction.upper(),
    )
    kpi3.metric(
        "95% Confidence Interval",
        f"[{trend_result.ci_lower:+.4f}, {trend_result.ci_upper:+.4f}]",
        f"Level: {trend_result.ci_level*100:.0f}%",
    )
    kpi4.metric(
        "Missing Data",
        f"{trend_result.missing_data_pct:.1f}%",
        "Quality: High" if trend_result.missing_data_pct < 5.0 else "Gaps Identified",
    )

    st.markdown("---")

    # 2. Main Time Series & Trend Line Visualization
    st.markdown("### 1. Historical Observation Series & Fitted Trend")

    # Compute OLS for comparison
    ols_slope, ols_intercept, ols_r2 = linear_trend(timestamps, values)
    ols_trend_y = ols_intercept + ols_slope * timestamps

    ts_df = pd.DataFrame({
        "Timestamp": timestamps,
        "Observed": values,
        "Theil-Sen Trend": viz_data.trend_line_y if viz_data.trend_line_y else None,
        "OLS Linear Trend": ols_trend_y,
    }).set_index("Timestamp")

    st.line_chart(ts_df, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.caption(
            f"**Theil-Sen Robust Slope**: `{trend_result.sens_slope:+.6f}` {trend_result.slope_unit} "
            f"(Resistant to weather anomalies and sensor dropouts; 29.3% breakdown point)."
        )
    with c2:
        st.caption(
            f"**Ordinary Least Squares (OLS)**: `{ols_slope*10.0:+.6f}` {trend_result.slope_unit} "
            f"(R² = {ols_r2:.3f}; vulnerable to heavy-tailed non-Gaussian distribution)."
        )

    st.markdown("---")

    # 3. Climatological Anomaly Chart
    st.markdown("### 2. Climatological Anomalies Relative to Baseline Mean")
    try:
        anomalies, baseline_mean = calculate_anomalies(values, period=12)
        anomaly_df = pd.DataFrame({
            "Timestamp": timestamps,
            "Anomaly": anomalies,
        }).set_index("Timestamp")

        st.bar_chart(anomaly_df, use_container_width=True)
        st.caption(
            f"Monthly deviation from multi-decadal climatological baseline mean ({baseline_mean:.2f} {series_data['unit']}). "
            "Peaks indicate extreme seasonal pulses; troughs highlight prolonged regional deficits."
        )
    except Exception as e:
        st.warning(f"Could not compute anomalies: {e}")

    st.markdown("---")

    # 4. Classical Seasonal Decomposition
    st.markdown("### 3. Additive Seasonal Decomposition (Trend, Seasonality, Residual)")
    try:
        trend_comp, seasonal_comp, resid_comp = seasonal_decompose(values, period=12)
        decomp_df = pd.DataFrame({
            "Timestamp": timestamps,
            "Trend Component": trend_comp,
            "Seasonal Component": seasonal_comp,
            "Stochastic Residual": resid_comp,
        }).set_index("Timestamp")

        st.line_chart(decomp_df[["Trend Component", "Seasonal Component"]], use_container_width=True)
        st.line_chart(decomp_df[["Stochastic Residual"]], use_container_width=True)
        st.caption(
            "Centered moving-average decomposition isolates repeating intra-annual oscillations from secular drift "
            "and stochastic weather noise."
        )
    except Exception as e:
        st.info(f"Seasonal decomposition requires continuous data: {e}")
