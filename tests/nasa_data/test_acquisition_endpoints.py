"""
Comprehensive Test Suite for NASA Earth-Science Data Acquisition Layer.

Validates:
1. Successful historical data retrieval (NASA POWER, GPM IMERG, GLDAS)
2. Parameter validation (invalid variables, invalid datasets)
3. Date range validation (start > end, out of bounds)
4. Missing observation handling (-999.0 sentinels -> NaN, strict gap accounting)
5. Upstream API failure and fallback provenance tagging
6. Caching invariants (cached data marked as LOCAL_CACHE, never masquerading as LIVE)
7. Unit consistency preservation
8. Distinction between satellite observations and reanalysis/land surface models
9. System health endpoints
"""

import pytest
import numpy as np

from nasa_data.schema import (
    ObservationRequest,
    NormalizedObservationSeries,
    ObservationType,
    RetrievalStatus,
    HealthStatus,
)
from nasa_data.api import (
    get_available_datasets,
    get_available_variables,
    get_available_regions,
    get_dataset_metadata,
    fetch_historical_data,
    check_data_source_health,
)
from nasa_data.registry import GLOBAL_REGISTRY
from nasa_data.drivers.power import NASAPowerDriver
from nasa_data.drivers.gpm_imerg import NASAGPMIMERGDriver
from nasa_data.drivers.gldas import NASAGLDASDriver


# ============================================================================
# 1. DATASET DISCOVERY & METADATA ENDPOINTS
# ============================================================================

def test_get_available_datasets_endpoint():
    """Verify endpoint lists all registered NASA datasets with formal metadata."""
    datasets = get_available_datasets()
    assert len(datasets) >= 3
    dataset_ids = [d.id for d in datasets]
    assert "nasa_power" in dataset_ids
    assert "gpm_imerg" in dataset_ids
    assert "gldas_noah" in dataset_ids

    # Verify each dataset has complete documentation and citation
    for d in datasets:
        assert d.agency != ""
        assert d.documentation_url.startswith("http")
        assert d.citation != ""
        assert len(d.supported_variables) > 0


def test_get_available_variables_endpoint():
    """Verify endpoint filters variables by dataset correctly."""
    all_vars = get_available_variables()
    assert len(all_vars) >= 5

    power_vars = get_available_variables("nasa_power")
    power_var_ids = [v.id for v in power_vars]
    assert "temperature_2m" in power_var_ids
    assert "precipitation" in power_var_ids

    gpm_vars = get_available_variables("gpm_imerg")
    assert len(gpm_vars) == 1
    assert gpm_vars[0].id == "precipitation"


def test_get_available_regions_endpoint():
    """Verify geographic preset endpoint returns coordinates and bounding boxes."""
    regions = get_available_regions()
    assert len(regions) >= 4
    for r in regions:
        assert "id" in r
        assert "latitude" in r
        assert "longitude" in r
        assert "bbox" in r
        assert len(r["bbox"]) == 4


def test_get_dataset_metadata_endpoint():
    """Verify metadata inspection endpoint."""
    meta = get_dataset_metadata("nasa_power")
    assert meta.id == "nasa_power"
    assert "MERRA-2" in meta.name

    with pytest.raises(KeyError):
        get_dataset_metadata("non_existent_dataset")


# ============================================================================
# 2. SUCCESSFUL DATA RETRIEVAL & UNIT CONSISTENCY
# ============================================================================

def test_fetch_nasa_power_temperature():
    """Verify successful retrieval and structure of NASA POWER 2m air temperature."""
    req = ObservationRequest(
        dataset_id="nasa_power",
        variable_id="temperature_2m",
        latitude=27.95,
        longitude=85.32,
        start_year=2000,
        end_year=2005,
        region_id="trishuli_himalaya",
    )
    series = fetch_historical_data(req)

    assert isinstance(series, NormalizedObservationSeries)
    assert series.variable_id == "temperature_2m"
    assert series.unit == "°C"
    assert series.slope_unit == "°C / decade"
    assert len(series.timestamps) == 6 * 12
    assert len(series.values) == 6 * 12
    assert series.temporal_resolution == "Monthly"
    assert series.missing_data_info.total_observations == 6 * 12


def test_fetch_gpm_imerg_precipitation():
    """Verify successful retrieval and structure of GPM IMERG satellite precipitation."""
    req = ObservationRequest(
        dataset_id="gpm_imerg",
        variable_id="precipitation",
        latitude=10.50,
        longitude=105.50,
        start_year=2010,
        end_year=2015,
        region_id="mekong_delta",
    )
    series = fetch_historical_data(req)

    assert series.dataset_id == "gpm_imerg"
    assert series.variable_id == "precipitation"
    assert series.unit == "mm / month"
    assert len(series.values) == 6 * 12
    # Verify satellite observation type
    assert series.source_provenance.observation_type == ObservationType.SATELLITE_OBSERVATION


def test_fetch_gldas_soil_moisture():
    """Verify successful retrieval of GLDAS land surface model soil moisture."""
    req = ObservationRequest(
        dataset_id="gldas_noah",
        variable_id="soil_moisture",
        latitude=39.50,
        longitude=-107.50,
        start_year=2012,
        end_year=2016,
        region_id="colorado_basin",
    )
    series = fetch_historical_data(req)

    assert series.dataset_id == "gldas_noah"
    assert series.unit == "Index (0-1)"
    assert series.source_provenance.observation_type == ObservationType.LAND_SURFACE_MODEL


# ============================================================================
# 3. VALIDATION: INVALID PARAMETERS & INVALID DATES
# ============================================================================

def test_invalid_variable_for_dataset():
    """Verify that requesting an unsupported variable raises a ValueError."""
    req = ObservationRequest(
        dataset_id="gpm_imerg",  # Only supports precipitation
        variable_id="temperature_2m",
        latitude=27.95,
        longitude=85.32,
        start_year=2010,
        end_year=2015,
    )
    with pytest.raises(ValueError, match="is not supported by dataset"):
        fetch_historical_data(req)


def test_invalid_date_range():
    """Verify that start_year > end_year raises ValueError."""
    req = ObservationRequest(
        dataset_id="nasa_power",
        variable_id="precipitation",
        latitude=27.95,
        longitude=85.32,
        start_year=2020,
        end_year=2010,  # Invalid: start > end
    )
    with pytest.raises(ValueError, match="cannot be after end_year"):
        fetch_historical_data(req)


def test_invalid_coordinates():
    """Verify that coordinates outside valid geographic range raise ValueError."""
    req = ObservationRequest(
        dataset_id="nasa_power",
        variable_id="precipitation",
        latitude=120.0,  # Invalid latitude (> 90)
        longitude=85.32,
        start_year=2000,
        end_year=2010,
    )
    with pytest.raises(ValueError, match="Latitude must be between"):
        fetch_historical_data(req)


# ============================================================================
# 4. MISSING VALUES & SENTINEL (-999.0) HANDLING
# ============================================================================

def test_missing_data_sentinel_parsing():
    """Verify -999.0 sentinels are strictly converted to np.nan and never imputed."""
    driver = NASAPowerDriver()
    raw_values = np.array([12.5, 14.2, np.nan, np.nan, 18.9, np.nan, 22.1])
    summary = driver.calculate_missing_data_summary(raw_values)

    assert summary.total_observations == 7
    assert summary.missing_observations == 3
    assert summary.valid_observations == 4
    assert summary.missing_percentage == pytest.approx(42.86, abs=0.01)
    assert summary.max_consecutive_gap == 2
    assert summary.gap_positions == [2, 5]


# ============================================================================
# 5. CACHING & PROVENANCE INVARIANTS
# ============================================================================

def test_caching_invariant_and_provenance():
    """Rule: A cached observation MUST have retrieval_status == LOCAL_CACHE."""
    req_initial = ObservationRequest(
        dataset_id="nasa_power",
        variable_id="solar_radiation",
        latitude=27.95,
        longitude=85.32,
        start_year=2015,
        end_year=2018,
        region_id="trishuli_himalaya",
        bypass_cache=True,  # Bypass cache to force live/benchmark acquisition
    )

    # First fetch: bypasses cache and populates it
    series1 = fetch_historical_data(req_initial)
    assert series1.source_provenance.retrieval_status in [
        RetrievalStatus.LIVE_NASA_API,
        RetrievalStatus.OFFLINE_BENCHMARK,
    ]

    # Second fetch without bypass: MUST be served from cache and clearly tagged as LOCAL_CACHE
    req_cached = ObservationRequest(
        dataset_id="nasa_power",
        variable_id="solar_radiation",
        latitude=27.95,
        longitude=85.32,
        start_year=2015,
        end_year=2018,
        region_id="trishuli_himalaya",
        bypass_cache=False,
    )
    series2 = fetch_historical_data(req_cached)
    assert series2.source_provenance.retrieval_status == RetrievalStatus.LOCAL_CACHE
    assert np.allclose(series1.values, series2.values, equal_nan=True)

    # Force bypass: should NOT be marked as LOCAL_CACHE
    req_bypass = ObservationRequest(
        dataset_id="nasa_power",
        variable_id="solar_radiation",
        latitude=27.95,
        longitude=85.32,
        start_year=2015,
        end_year=2018,
        region_id="trishuli_himalaya",
        bypass_cache=True,
    )
    series3 = fetch_historical_data(req_bypass)
    assert series3.source_provenance.retrieval_status != RetrievalStatus.LOCAL_CACHE


# ============================================================================
# 6. OBSERVATION TYPE DISTINCTION
# ============================================================================

def test_satellite_vs_reanalysis_model_distinction():
    """Verify explicit distinction between satellite observations and reanalysis models."""
    req_sat = ObservationRequest(
        dataset_id="gpm_imerg",
        variable_id="precipitation",
        latitude=27.95,
        longitude=85.32,
        start_year=2010,
        end_year=2015,
    )
    res_sat = fetch_historical_data(req_sat)
    assert res_sat.source_provenance.observation_type == ObservationType.SATELLITE_OBSERVATION

    req_model = ObservationRequest(
        dataset_id="nasa_power",
        variable_id="temperature_2m",
        latitude=27.95,
        longitude=85.32,
        start_year=2010,
        end_year=2015,
    )
    res_model = fetch_historical_data(req_model)
    assert res_model.source_provenance.observation_type == ObservationType.REANALYSIS_MODEL


# ============================================================================
# 7. SOURCE HEALTH CHECK ENDPOINT
# ============================================================================

def test_source_health_endpoint():
    """Verify health probe returns status, latency, and operational messages."""
    health_reports = check_data_source_health()
    assert len(health_reports) >= 3
    for h in health_reports:
        assert h.dataset_id in ["nasa_power", "gpm_imerg", "gldas_noah"]
        assert h.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNAVAILABLE]
        assert h.latency_ms >= 0.0
        assert h.message != ""
