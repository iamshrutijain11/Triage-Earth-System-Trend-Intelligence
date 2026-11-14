"""
Trend direction classification and statistical interpretation.

Classifies trends based on BOTH the slope AND statistical significance.
A trend is NEVER classified as significant based only on its slope.
"""

from __future__ import annotations

from typing import Literal


def classify_trend(
    sens_slope: float,
    p_value: float,
    alpha: float = 0.05,
    slope_threshold: float = 0.0,
) -> Literal["increasing", "decreasing", "no trend"]:
    """Classify trend direction.

    Rules (per statistical requirements):
    - A trend is "increasing" only if slope > 0 AND p < alpha.
    - A trend is "decreasing" only if slope < 0 AND p < alpha.
    - Otherwise, "no trend" — even if the slope is nonzero but
      not statistically significant.

    Parameters
    ----------
    sens_slope : float
        Sen's slope value.
    p_value : float
        p-value from Mann-Kendall test.
    alpha : float
        Significance threshold.
    slope_threshold : float
        Optional minimum absolute slope for classification.
        Default 0.0 (any nonzero slope with significant p).

    Returns
    -------
    direction : str
    """
    if p_value >= alpha:
        return "no trend"

    if abs(sens_slope) <= slope_threshold:
        return "no trend"

    return "increasing" if sens_slope > 0 else "decreasing"


def interpret_result(
    variable_name: str,
    trend_direction: str,
    sens_slope: float,
    slope_unit: str,
    p_value: float,
    alpha: float,
    ci_lower: float,
    ci_upper: float,
    missing_pct: float,
    autocorrelation_corrected: bool = False,
) -> str:
    """Generate a human-readable statistical interpretation.

    Distinguishes statistical significance from practical importance.

    Returns
    -------
    interpretation : str
    """
    parts = []

    # Trend statement
    if trend_direction == "no trend":
        parts.append(
            f"No statistically significant trend was detected in "
            f"{variable_name} (p = {p_value:.4f}, α = {alpha:.2f})."
        )
    else:
        parts.append(
            f"A statistically significant {trend_direction} trend was "
            f"detected in {variable_name} (p = {p_value:.4f}, α = {alpha:.2f})."
        )

    # Slope
    parts.append(
        f"Sen's slope: {sens_slope:+.6f} {slope_unit} "
        f"(95% CI: [{ci_lower:+.6f}, {ci_upper:+.6f}])."
    )

    # Practical significance caveat
    if trend_direction != "no trend":
        parts.append(
            "NOTE: Statistical significance does not necessarily imply "
            "practical importance. The magnitude of this trend should be "
            "evaluated against domain-specific thresholds and the variable's "
            "natural variability."
        )

    # Data quality
    if missing_pct > 0:
        parts.append(
            f"Data completeness: {100.0 - missing_pct:.1f}% "
            f"({missing_pct:.1f}% missing observations)."
        )
        if missing_pct > 20:
            parts.append(
                "WARNING: >20% missing data may affect reliability of the "
                "trend estimate."
            )

    # Autocorrelation
    if autocorrelation_corrected:
        parts.append(
            "Autocorrelation correction (Hamed & Rao, 1998) was applied "
            "to account for serial dependence in the data."
        )

    return " ".join(parts)


def describe_methodology(
    is_seasonal: bool,
    has_autocorrelation: bool,
    n_grid_cells: int = 0,
) -> str:
    """Return the analysis method description string."""
    parts = []

    if is_seasonal:
        parts.append("Seasonal Mann-Kendall test (Hirsch et al., 1982)")
    else:
        parts.append("Mann-Kendall test (Mann, 1945; Kendall, 1975)")

    parts.append("with Sen's slope estimator (Sen, 1968)")

    if has_autocorrelation:
        parts.append(
            "and Hamed & Rao (1998) variance correction for serial autocorrelation"
        )

    if n_grid_cells > 1:
        parts.append(
            f"with Benjamini-Hochberg FDR correction for {n_grid_cells} "
            "spatial grid cells"
        )

    return ", ".join(parts) + "."


def describe_limitations(
    missing_pct: float,
    n_obs: int,
    is_seasonal: bool,
    has_autocorrelation: bool,
) -> str:
    """Generate methodological limitations text."""
    limitations = []

    if n_obs < 30:
        limitations.append(
            f"Short record length ({n_obs} observations) limits statistical power."
        )

    if missing_pct > 5:
        limitations.append(
            f"Missing data ({missing_pct:.1f}%) may introduce bias if gaps "
            "are not randomly distributed."
        )

    if has_autocorrelation:
        limitations.append(
            "Serial autocorrelation was detected and corrected, but the "
            "correction assumes a specific autocorrelation structure."
        )

    if is_seasonal:
        limitations.append(
            "The seasonal Mann-Kendall test assumes homogeneity of trend "
            "direction across all seasons."
        )

    limitations.append(
        "Non-parametric tests make no assumptions about the distribution "
        "of the data but have less statistical power than parametric "
        "alternatives when data are normally distributed."
    )

    return " ".join(limitations) if limitations else "None identified."
