"""
Data models for trend analysis results.

Structured output classes that capture every required field for
reproducible statistical reporting.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal, Tuple, Dict, Any


@dataclass
class TrendResult:
    """Complete statistical trend analysis result for one variable/region.

    Every field required by the NASA Space Apps challenge specification
    is represented here.
    """

    # --- Identification ---
    variable_name: str
    dataset: str
    unit: str

    # --- Observation metadata ---
    observation_count: int
    observation_period: str  # e.g. "1980-01 to 2024-12"
    missing_data_pct: float  # percentage, 0-100

    # --- Trend estimation ---
    trend_direction: Literal["increasing", "decreasing", "no trend"]
    sens_slope: float
    slope_unit: str  # e.g. "°C / decade", "mm / year"

    # --- Significance testing ---
    mk_statistic: float  # Mann-Kendall S statistic
    mk_z: float  # Normalized Z statistic
    p_value: float
    significance_threshold: float = 0.05
    is_statistically_significant: bool = False

    # --- Confidence interval ---
    ci_lower: float = 0.0
    ci_upper: float = 0.0
    ci_level: float = 0.95  # confidence level

    # --- Methodology ---
    analysis_method: str = ""  # e.g. "Seasonal Mann-Kendall with autocorrelation correction"
    methodological_limitations: str = ""

    # --- Autocorrelation ---
    autocorrelation_lag1: Optional[float] = None
    autocorrelation_significant: Optional[bool] = None
    variance_correction_factor: Optional[float] = None

    # --- Multiple testing (for spatial grids) ---
    adjusted_p_value: Optional[float] = None
    multiple_testing_method: Optional[str] = None

    @property
    def measurement_unit(self) -> str:
        """Alias matching NASA challenge specification."""
        return self.unit

    @property
    def confidence_interval(self) -> Tuple[float, float]:
        """(ci_lower, ci_upper) tuple at ci_level confidence."""
        return (self.ci_lower, self.ci_upper)

    @property
    def statistical_significance(self) -> bool:
        """Alias matching NASA challenge specification."""
        return self.is_statistically_significant

    @property
    def missing_data_percentage(self) -> float:
        """Alias matching NASA challenge specification."""
        return self.missing_data_pct

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON/API output with all challenge-specified fields."""
        d = asdict(self)
        d["measurement_unit"] = self.measurement_unit
        d["confidence_interval"] = [self.ci_lower, self.ci_upper]
        d["statistical_significance"] = self.statistical_significance
        d["missing_data_percentage"] = self.missing_data_percentage
        return d

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @property
    def practical_significance_note(self) -> str:
        """Distinguish statistical significance from practical importance."""
        if not self.is_statistically_significant:
            return (
                "The trend is NOT statistically significant at the "
                f"{self.significance_threshold:.2f} level. "
                "Any observed slope may be due to natural variability."
            )
        # Significant — note that statistical ≠ practical
        return (
            f"The trend IS statistically significant (p={self.p_value:.4f}). "
            f"However, statistical significance does not automatically imply "
            f"practical importance. The magnitude of the trend "
            f"({self.sens_slope:.6f} {self.slope_unit}) should be evaluated "
            f"in the context of the variable's natural variability and the "
            f"application domain."
        )


@dataclass
class VisualizationData:
    """Structured data bundle for generating trend visualizations."""

    # Time-series chart data
    timestamps: list = field(default_factory=list)
    values: list = field(default_factory=list)

    # Trend line
    trend_line_x: list = field(default_factory=list)
    trend_line_y: list = field(default_factory=list)

    # Anomaly chart
    anomalies: list = field(default_factory=list)
    anomaly_baseline: Optional[float] = None

    # Confidence interval bands
    ci_upper_band: list = field(default_factory=list)
    ci_lower_band: list = field(default_factory=list)

    # Seasonal decomposition
    seasonal_component: list = field(default_factory=list)
    trend_component: list = field(default_factory=list)
    residual_component: list = field(default_factory=list)

    # Regional comparison
    region_labels: list = field(default_factory=list)
    region_slopes: list = field(default_factory=list)
    region_p_values: list = field(default_factory=list)

    # Geographical map data
    grid_lats: list = field(default_factory=list)
    grid_lons: list = field(default_factory=list)
    grid_slopes: list = field(default_factory=list)
    grid_significant: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
