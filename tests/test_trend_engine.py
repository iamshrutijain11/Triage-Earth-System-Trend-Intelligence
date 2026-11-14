"""
Comprehensive unit and integration test suite for the Statistical Trend-Analysis Engine.

Validates:
1. The 7 canonical synthetic benchmark datasets
2. Core statistical principles:
   - Sen's slope calculation and confidence interval
   - Mann-Kendall significance testing (standard vs seasonal)
   - Autocorrelation detection and Hamed-Rao variance correction
   - Multiple hypothesis testing (Benjamini-Hochberg FDR, Bonferroni)
   - Rule enforcement: No trend classified as significant based solely on slope
   - Missing data handling (NaN robustness)
3. API endpoints and serialization
"""

import pytest
import numpy as np

from trend_engine.models import TrendResult, VisualizationData
from trend_engine.analyzer import TrendAnalyzer
from trend_engine.synthetic import generate_synthetic_datasets
from trend_engine.timeseries import (
    build_timeseries,
    calculate_missing_data_stats,
    dropna_paired,
)
from trend_engine.decomposition import (
    seasonal_decompose,
    calculate_anomalies,
    calculate_annual_anomalies,
)
from trend_engine.trends import (
    sens_slope,
    sens_slope_confidence_interval,
    linear_trend,
)
from trend_engine.significance import (
    mann_kendall,
    seasonal_mann_kendall,
    mann_kendall_corrected,
    lag1_autocorrelation,
    is_autocorrelation_significant,
)
from trend_engine.confidence import (
    slope_confidence_interval,
    benjamini_hochberg,
    bonferroni,
)
from trend_engine.classification import (
    classify_trend,
    interpret_result,
    describe_methodology,
    describe_limitations,
)
from trend_engine.api import (
    analyze_variable,
    compare_regions,
    analyze_spatial_grid,
)


# ============================================================================
# 1. SYNTHETIC BENCHMARK VALIDATION (7 CANONICAL CASES)
# ============================================================================

@pytest.fixture(scope="module")
def synthetic_data():
    return generate_synthetic_datasets(seed=12345)


def test_synthetic_case_1_clearly_increasing(synthetic_data):
    """Case 1: Clearly increasing trend must be identified as increasing."""
    ds = synthetic_data["increasing"]
    analyzer = TrendAnalyzer(alpha=0.05)
    res = analyzer.analyze(
        timestamps=ds["timestamps"],
        values=ds["values"],
        variable_name="Surface Temperature",
        dataset="Synthetic",
        unit="°C",
        is_seasonal=False,
    )
    assert res.trend_direction == "increasing"
    assert res.is_statistically_significant is True
    assert res.p_value < 0.05
    assert res.sens_slope > 0
    # True slope was 0.08, estimated slope should be close
    assert np.isclose(res.sens_slope, ds["true_slope"], atol=0.03)
    assert res.ci_lower < res.sens_slope < res.ci_upper


def test_synthetic_case_2_clearly_decreasing(synthetic_data):
    """Case 2: Clearly decreasing trend must be identified as decreasing."""
    ds = synthetic_data["decreasing"]
    analyzer = TrendAnalyzer(alpha=0.05)
    res = analyzer.analyze(
        timestamps=ds["timestamps"],
        values=ds["values"],
        variable_name="Snow Cover Extent",
        dataset="Synthetic",
        unit="km²",
        is_seasonal=False,
    )
    assert res.trend_direction == "decreasing"
    assert res.is_statistically_significant is True
    assert res.p_value < 0.05
    assert res.sens_slope < 0
    assert np.isclose(res.sens_slope, ds["true_slope"], atol=0.03)


def test_synthetic_case_3_stationary(synthetic_data):
    """Case 3: Stationary white noise series must be classified as 'no trend'."""
    ds = synthetic_data["stationary"]
    analyzer = TrendAnalyzer(alpha=0.05)
    res = analyzer.analyze(
        timestamps=ds["timestamps"],
        values=ds["values"],
        variable_name="Relative Humidity",
        dataset="Synthetic",
        unit="%",
        is_seasonal=False,
    )
    assert res.trend_direction == "no trend"
    assert res.is_statistically_significant is False
    assert res.p_value >= 0.05


def test_synthetic_case_4_seasonal_no_trend(synthetic_data):
    """Case 4: Pure seasonal cycle with no trend.

    Must NOT produce a false trend when using Seasonal Mann-Kendall.
    """
    ds = synthetic_data["seasonal_no_trend"]
    analyzer = TrendAnalyzer(alpha=0.05)
    res = analyzer.analyze(
        timestamps=ds["timestamps"],
        values=ds["values"],
        variable_name="Monthly Precipitation",
        dataset="Synthetic",
        unit="mm",
        is_seasonal=True,
        period=12,
    )
    assert res.trend_direction == "no trend"
    assert res.is_statistically_significant is False
    assert res.p_value >= 0.05
    assert "Seasonal Mann-Kendall" in res.analysis_method


def test_synthetic_case_5_seasonal_with_trend(synthetic_data):
    """Case 5: Seasonal cycle with underlying positive trend.

    Seasonal Mann-Kendall must detect the trend despite large seasonal swings.
    """
    ds = synthetic_data["seasonal_with_trend"]
    analyzer = TrendAnalyzer(alpha=0.05)
    res = analyzer.analyze(
        timestamps=ds["timestamps"],
        values=ds["values"],
        variable_name="Monthly Temperature",
        dataset="Synthetic",
        unit="°C",
        is_seasonal=True,
        period=12,
        slope_per="step",
    )
    assert res.trend_direction == "increasing"
    assert res.is_statistically_significant is True
    assert res.p_value < 0.05
    assert res.sens_slope > 0


def test_synthetic_case_6_missing_observations(synthetic_data):
    """Case 6: Time series with 20% random missing observations.

    Engine must accurately report missing % and compute trend without crashing.
    """
    ds = synthetic_data["missing_data"]
    analyzer = TrendAnalyzer(alpha=0.05)
    res = analyzer.analyze(
        timestamps=ds["timestamps"],
        values=ds["values"],
        variable_name="Sea Surface Salinity",
        dataset="Synthetic",
        unit="PSU",
        is_seasonal=False,
    )
    assert res.missing_data_pct == pytest.approx(20.0, abs=1.0)
    assert res.observation_count == int(len(ds["values"]) * 0.8)
    assert res.trend_direction == "increasing"
    assert res.is_statistically_significant is True


def test_synthetic_case_7_autocorrelation_handling(synthetic_data):
    """Case 7: Stationary AR(1) series with significant autocorrelation.

    Autocorrelation must be detected, variance correction factor applied,
    and no spurious trend should be declared.
    """
    ds = synthetic_data["autocorrelated"]
    analyzer = TrendAnalyzer(alpha=0.05)
    res = analyzer.analyze(
        timestamps=ds["timestamps"],
        values=ds["values"],
        variable_name="Geopotential Height",
        dataset="Synthetic",
        unit="m",
        is_seasonal=False,
    )
    # Autocorrelation must be flagged
    assert res.autocorrelation_significant is True
    assert res.autocorrelation_lag1 is not None and res.autocorrelation_lag1 > 0.4
    # Variance correction should have been applied (factor > 1.0)
    assert res.variance_correction_factor is not None
    assert res.variance_correction_factor > 1.0
    # Should not classify stationary AR(1) as significant trend
    assert res.trend_direction == "no trend"


# ============================================================================
# 2. STATISTICAL RULE ENFORCEMENT & EDGE CASES
# ============================================================================

def test_never_classify_significant_based_solely_on_slope():
    """Rule: A large slope with high p-value must NOT be classified as significant."""
    direction = classify_trend(sens_slope=150.0, p_value=0.25, alpha=0.05)
    assert direction == "no trend"

    direction = classify_trend(sens_slope=-99.0, p_value=0.08, alpha=0.05)
    assert direction == "no trend"


def test_classify_trend_direction_logic():
    """Verify standard classification transitions."""
    assert classify_trend(sens_slope=0.5, p_value=0.01, alpha=0.05) == "increasing"
    assert classify_trend(sens_slope=-0.5, p_value=0.01, alpha=0.05) == "decreasing"
    assert classify_trend(sens_slope=0.0, p_value=0.01, alpha=0.05) == "no trend"


def test_confidence_interval_bounds():
    """Sen's slope CI must bracket the median slope."""
    t = np.arange(50, dtype=float)
    y = 2.0 * t + np.random.normal(0, 1.0, size=50)
    slope, intercept, _ = sens_slope(t, y)
    lo, hi = sens_slope_confidence_interval(t, y, alpha=0.05)
    assert lo <= slope <= hi


def test_multiple_testing_correction_fdr_and_bonferroni():
    """Verify Benjamini-Hochberg and Bonferroni adjustments."""
    raw_p = np.array([0.001, 0.01, 0.04, 0.06, 0.50])
    adj_fdr, sig_fdr = benjamini_hochberg(raw_p, alpha=0.05)
    adj_bonf, sig_bonf = bonferroni(raw_p, alpha=0.05)

    # Bonferroni should be >= raw_p * m
    assert np.all(adj_bonf >= raw_p)
    # Bonferroni is always >= FDR
    assert np.all(adj_bonf >= adj_fdr)
    # The lowest p-value (0.001) should remain significant under both
    assert sig_fdr[0] and sig_bonf[0]


def test_seasonal_decomposition_components():
    """Additive seasonal decomposition sums back to original series."""
    t = np.arange(48, dtype=float)
    trend_true = 0.5 * t
    seasonal_true = np.tile([5, 10, -5, -10], 12)
    series = trend_true + seasonal_true

    trend_est, seasonal_est, resid_est = seasonal_decompose(series, period=4)
    valid_idx = ~np.isnan(trend_est)

    reconstructed = trend_est[valid_idx] + seasonal_est[valid_idx] + resid_est[valid_idx]
    assert np.allclose(reconstructed, series[valid_idx], atol=1e-5)


def test_missing_data_diagnostics():
    """Missing data diagnostic correctly identifies consecutive gap lengths."""
    vals = np.array([1.0, 2.0, np.nan, np.nan, np.nan, 3.0, np.nan, 4.0])
    stats = calculate_missing_data_stats(vals)
    assert stats["total"] == 8
    assert stats["missing"] == 4
    assert stats["valid"] == 4
    assert stats["missing_pct"] == 50.0
    assert stats["max_consecutive_gap"] == 3


# ============================================================================
# 3. HIGH-LEVEL API ENDPOINTS & OUTPUT CONTRACTS
# ============================================================================

def test_analyze_variable_api_contract():
    """API endpoint returns all required fields in the expected types."""
    t = np.arange(30, dtype=float)
    v = 0.5 * t + np.random.normal(0, 0.2, size=30)

    res = analyze_variable(
        timestamps=t,
        values=v,
        variable_name="Atmospheric CO2",
        dataset="OCO-2",
        unit="ppm",
        is_seasonal=False,
        include_visualization=True,
    )

    assert "result" in res
    assert "interpretation" in res
    assert "visualization" in res

    r = res["result"]
    # Check all required specification fields exist
    expected_fields = [
        "variable_name", "dataset", "unit", "observation_count",
        "observation_period", "trend_direction", "sens_slope",
        "slope_unit", "mk_statistic", "p_value", "ci_lower", "ci_upper",
        "is_statistically_significant", "missing_data_pct",
        "analysis_method", "methodological_limitations",
    ]
    for field in expected_fields:
        assert field in r, f"Missing required output field: {field}"


def test_compare_regions_api():
    """Compare trends across regions with FDR adjustment."""
    t = np.arange(40, dtype=float)
    r1 = {
        "timestamps": t,
        "values": 0.4 * t + np.random.normal(0, 0.2, size=40),
        "variable_name": "LST",
        "dataset": "Region_A",
        "unit": "K",
    }
    r2 = {
        "timestamps": t,
        "values": np.random.normal(300, 1.0, size=40),
        "variable_name": "LST",
        "dataset": "Region_B",
        "unit": "K",
    }

    comp = compare_regions([r1, r2], correction_method="fdr")
    assert len(comp["results"]) == 2
    assert len(comp["corrected_p_values"]) == 2
    assert comp["correction_method"] == "FDR"
    assert "visualization" in comp


def test_analyze_spatial_grid_api():
    """Grid-cell spatial analysis with FDR control."""
    lats = np.array([27.5, 27.6, 27.7])
    lons = np.array([85.1, 85.2, 85.3])
    t = np.arange(30, dtype=float)

    grid_ts = [
        0.5 * t + np.random.normal(0, 0.2, 30),
        -0.3 * t + np.random.normal(0, 0.2, 30),
        np.random.normal(0, 1.0, 30),
    ]

    out = analyze_spatial_grid(
        lats=lats,
        lons=lons,
        grid_timeseries=grid_ts,
        timestamps=t,
        variable_name="Precipitation",
        dataset="GPM_IMERG",
        unit="mm",
        slope_per="year",
        correction_method="fdr",
    )

    assert out["n_cells"] == 3
    assert len(out["corrected_p_values"]) == 3
    assert "visualization" in out
    assert out["visualization"]["grid_slopes"] is not None



def test_analyze_normalized_series_integration():
    """Verify end-to-end integration with NormalizedObservationSeries and challenge output contract."""
    from trend_engine.api import analyze_normalized_series
    from nasa_data.api import fetch_historical_data, ObservationRequest

    req = ObservationRequest(
        dataset_id="nasa_power",
        variable_id="temperature_2m",
        latitude=27.95,
        longitude=85.32,
        start_year=1990,
        end_year=2020,
        region_id="trishuli_himalaya",
    )
    series = fetch_historical_data(req)
    out = analyze_normalized_series(series, slope_per="decade", include_visualization=True)

    assert "result" in out
    assert "interpretation" in out
    assert "visualization" in out

    r = out["result"]

    # Explicit challenge-required keys
    challenge_required_keys = [
        "variable_name",
        "dataset",
        "measurement_unit",
        "observation_count",
        "observation_period",
        "trend_direction",
        "sens_slope",
        "slope_unit",
        "mk_statistic",
        "p_value",
        "confidence_interval",
        "statistical_significance",
        "missing_data_percentage",
        "analysis_method",
        "methodological_limitations",
    ]

    for key in challenge_required_keys:
        assert key in r, f"Key '{key}' missing from challenge required output contract!"

    # Verify structured visualization elements
    viz = out["visualization"]
    assert "timestamps" in viz
    assert "values" in viz
    assert "trend_line_x" in viz
    assert "trend_line_y" in viz
    assert "anomalies" in viz
    assert "ci_upper_band" in viz
    assert "ci_lower_band" in viz
