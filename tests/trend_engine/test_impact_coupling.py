"""
Unit tests for the Climate Trend Impact Coupling Module (trend_engine.impact).

Validates:
1. Impact vulnerability index (IVI) computation
2. Extreme event return period scaling for precipitation and temperature trends
3. Engineering directives and physical infrastructure implication generation
"""

import pytest
from trend_engine.models import TrendResult
from trend_engine.impact import assess_climate_trend_impact, ImpactAssessment


def test_positive_precipitation_trend_impact():
    """Verify that a significant increasing precipitation trend elevates flood risk."""
    tr = TrendResult(
        variable_name="Precipitation",
        dataset="GPM IMERG",
        unit="mm",
        observation_count=360,
        observation_period="1990-01 to 2019-12",
        missing_data_pct=0.0,
        trend_direction="increasing",
        sens_slope=2.5,
        slope_unit="mm / decade",
        mk_statistic=3200.0,
        mk_z=3.4,
        p_value=0.00067,
        significance_threshold=0.05,
        is_statistically_significant=True,
        ci_lower=1.2,
        ci_upper=3.8,
    )

    impact = assess_climate_trend_impact(
        trend_result=tr,
        region_name="Trishuli Basin",
        baseline_asset_summary={"total_damaged_buildings": 42, "total_damaged_roads_km": 12.5},
    )

    assert isinstance(impact, ImpactAssessment)
    assert impact.impact_vulnerability_index > 50.0
    assert impact.extreme_event_frequency_shift_pct > 0.0
    assert impact.impact_category in ["High", "Critical"]
    assert len(impact.infrastructure_implications) >= 2
    assert len(impact.tactical_recommendations) >= 2
    # Verify baseline assets were incorporated
    assert any("42 exposed buildings" in imp for imp in impact.infrastructure_implications)


def test_stationary_trend_impact():
    """Verify that a non-significant stationary trend defaults to baseline risk."""
    tr = TrendResult(
        variable_name="Surface Air Temperature",
        dataset="AIRS",
        unit="°C",
        observation_count=240,
        observation_period="2000-01 to 2019-12",
        missing_data_pct=0.0,
        trend_direction="no trend",
        sens_slope=0.01,
        slope_unit="°C / decade",
        mk_statistic=50.0,
        mk_z=0.2,
        p_value=0.84,
        significance_threshold=0.05,
        is_statistically_significant=False,
    )

    impact = assess_climate_trend_impact(
        trend_result=tr,
        region_name="Colorado Basin",
    )

    assert impact.impact_category in ["Low", "Moderate"]
    assert impact.extreme_event_frequency_shift_pct == 0.0
