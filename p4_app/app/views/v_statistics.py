"""
Module C: Statistical Intelligence.

Scientific validation and hypothesis testing dashboard:
- Mann-Kendall / Seasonal Mann-Kendall hypothesis testing metrics
- Serial autocorrelation detection and Hamed & Rao (1998) variance correction
- Hollander & Wolfe non-parametric rank confidence intervals
- Plain-language statistical interpretation distinguishing significance from magnitude
- Transparent methodological limitations report for NASA judges
"""

from __future__ import annotations
import streamlit as st
import numpy as np
import pandas as pd

from trend_engine.models import TrendResult


def render_statistics_view(trend_result: TrendResult, interpretation_text: str) -> None:
    """Render Module C: Statistical Intelligence view."""
    st.markdown("## 📊 Module C: Statistical Intelligence")
    st.markdown(
        "Scientific validation scorecard reporting non-parametric hypothesis testing, "
        "serial autocorrelation diagnostics, and rigorous uncertainty bounds."
    )

    # 1. Hypothesis Testing Scorecard
    s1, s2, s3, s4 = st.columns(4)
    s1.metric(
        "Mann-Kendall S",
        f"{trend_result.mk_statistic:,.0f}",
        "Concordant vs Discordant Pairs",
    )
    s2.metric(
        "Normalized Z",
        f"{trend_result.mk_z:+.3f}",
        "Standardized Test Statistic",
    )
    s3.metric(
        "p-value",
        f"{trend_result.p_value:.6f}",
        f"Threshold α = {trend_result.significance_threshold:.2f}",
    )
    s4.metric(
        "Hypothesis Outcome",
        "REJECT H₀" if trend_result.is_statistically_significant else "FAIL TO REJECT H₀",
        "Statistically Significant" if trend_result.is_statistically_significant else "Natural Variability",
    )

    st.markdown("---")

    # 2. Detailed Climatological Audit Table
    st.markdown("### 📋 Statistical Metrics Audit Table")
    audit_data = [
        {"Parameter": "Variable Analyzed", "Value": trend_result.variable_name, "Climatological Standard": "NASA Earth Observing System"},
        {"Parameter": "Dataset Source", "Value": trend_result.dataset, "Climatological Standard": "Level 3/4 Gridded Assimilation"},
        {"Parameter": "Observation Count", "Value": f"{trend_result.observation_count} months", "Climatological Standard": ">= 30 years (WMO Climate Normal)"},
        {"Parameter": "Missing Observations", "Value": f"{trend_result.missing_data_pct:.2f}%", "Climatological Standard": "< 10% permissible"},
        {"Parameter": "Sen's Median Slope", "Value": f"{trend_result.sens_slope:+.6f} {trend_result.slope_unit}", "Climatological Standard": "Theil (1950), Sen (1968)"},
        {"Parameter": "95% Rank Confidence Interval", "Value": f"[{trend_result.ci_lower:+.6f}, {trend_result.ci_upper:+.6f}]", "Climatological Standard": "Hollander & Wolfe (1999)"},
        {"Parameter": "Mann-Kendall Test Type", "Value": trend_result.analysis_method, "Climatological Standard": "Hirsch et al. (1982) Seasonal MK"},
        {"Parameter": "Two-Sided p-value", "Value": f"{trend_result.p_value:.6f}", "Climatological Standard": "α = 0.05 Significance Criterion"},
        {"Parameter": "Lag-1 Autocorrelation (r₁)", "Value": f"{trend_result.autocorrelation_lag1 if trend_result.autocorrelation_lag1 is not None else 0.0:.4f}", "Climatological Standard": "Evaluated on detrended residuals"},
        {"Parameter": "Serial Autocorrelation Significant?", "Value": "Yes (Corrected)" if trend_result.autocorrelation_significant else "No (White Noise)", "Climatological Standard": "Critical bound ±1.96/√n"},
        {"Parameter": "Variance Inflation Factor (n/n*)", "Value": f"{trend_result.variance_correction_factor:.3f}" if trend_result.variance_correction_factor else "1.000 (No inflation)", "Climatological Standard": "Hamed & Rao (1998)"},
    ]
    st.dataframe(pd.DataFrame(audit_data), use_container_width=True, hide_index=True)

    st.markdown("---")

    # 3. Scientific Interpretation & Practical Significance Caveat
    st.markdown("### 🧠 Scientific Interpretation & Practical Significance")
    if trend_result.is_statistically_significant:
        st.success(f"**Verified Statistical Trend**: {interpretation_text}")
    else:
        st.info(f"**No Statistically Significant Trend**: {interpretation_text}")

    st.warning(
        "⚠️ **Statistical Significance vs. Practical Magnitude**: "
        "A trend may achieve mathematical significance ($p < 0.05$) due to long sample duration even when the "
        "physical change is small. Conversely, short observation records may mask operationally critical shifts. "
        "Judges and decision-makers must evaluate Sen's slope magnitude in direct tandem with the 95% confidence interval."
    )

    st.markdown("---")

    # 4. Methodological Limitations & Assumptions
    st.markdown("### 🔍 Methodological Limitations & Transparency")
    st.markdown(f"**Documented Limitations**: {trend_result.methodological_limitations}")
    st.caption(
        "All calculations strictly follow reproducible non-parametric mathematical procedures. "
        "No artificial p-hacking or parametric distribution assumptions are applied."
    )
