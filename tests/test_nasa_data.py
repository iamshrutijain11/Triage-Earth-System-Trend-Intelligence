"""
Unit tests for the NASA Earth Observation Data Module (nasa_data).

Validates:
1. NASA variable catalog integrity and metadata completeness
2. Regional presets and geographic coordinate bounds
3. Curated benchmark series retrieval and climatological consistency
4. NASA client caching and fallback behavior
5. Spatial grid generation for regional atlas
"""

import pytest
import numpy as np

from nasa_data.catalog import NASA_CATALOG, REGIONAL_PRESETS, VariableMetadata
from nasa_data.local_store import get_curated_benchmark_series
from nasa_data.client import NASAClient
from nasa_data.reader import create_spatial_grid_from_bbox, generate_regional_grid_time_series


def test_catalog_completeness():
    """Verify that all major NASA Earth science variables are registered with units."""
    required_vars = ["precipitation", "temperature_2m", "soil_moisture", "ndvi", "solar_radiation"]
    for v_id in required_vars:
        assert v_id in NASA_CATALOG, f"Missing variable in NASA_CATALOG: {v_id}"
        meta = NASA_CATALOG[v_id]
        assert isinstance(meta, VariableMetadata)
        assert meta.unit != ""
        assert meta.slope_unit != ""
        assert meta.mission != ""
        assert meta.dataset_name != ""


def test_regional_presets_validity():
    """Verify geographic presets contain valid bounding box and coordinate tuples."""
    for r_id, r_info in REGIONAL_PRESETS.items():
        assert "bbox" in r_info
        bbox = r_info["bbox"]
        assert len(bbox) == 4
        min_lon, min_lat, max_lon, max_lat = bbox
        assert min_lon < max_lon
        assert min_lat < max_lat
        assert -180.0 <= min_lon <= 180.0
        assert -90.0 <= min_lat <= 90.0


def test_curated_benchmark_series_generation():
    """Verify that benchmark series have correct monthly lengths, non-empty values, and provenance."""
    series = get_curated_benchmark_series(
        variable_id="precipitation",
        region_id="trishuli_himalaya",
        start_year=1990,
        end_year=2020,
    )
    expected_months = (2020 - 1990 + 1) * 12
    assert len(series["timestamps"]) == expected_months
    assert len(series["values"]) == expected_months
    assert not np.all(np.isnan(series["values"]))
    assert np.all(series["values"] >= 0.0)  # Precipitation cannot be negative
    assert "provenance" in series
    assert series["provenance"]["agency"] == "NASA Earth Science Division"


def test_nasa_client_fetch_and_cache(tmp_path):
    """Verify NASAClient fetches, parses, and caches multi-decadal series."""
    client = NASAClient(cache_dir=str(tmp_path))
    res = client.fetch_time_series(
        variable_id="temperature_2m",
        region_id="trishuli_himalaya",
        start_year=1995,
        end_year=2005,
    )
    assert len(res["values"]) == 11 * 12
    assert res["unit"] == "°C"
    assert "timestamps" in res

    # Verify cache file was written
    cache_files = list(tmp_path.glob("*.json"))
    assert len(cache_files) >= 1


def test_spatial_grid_generation():
    """Verify spatial grid synthesis for the regional atlas."""
    bbox = [85.10, 27.75, 85.55, 28.25]
    lats, lons = create_spatial_grid_from_bbox(bbox, n_lat=3, n_lon=3)
    assert len(lats) == 3
    assert len(lons) == 3

    base_ts = np.arange(24, dtype=float)
    base_vals = np.ones(24) * 20.0
    g_lats, g_lons, g_series = generate_regional_grid_time_series(
        bbox=bbox,
        variable_id="precipitation",
        base_timestamps=base_ts,
        base_values=base_vals,
        n_lat=3,
        n_lon=3,
    )
    assert len(g_lats) == 9
    assert len(g_lons) == 9
    assert len(g_series) == 9
    assert len(g_series[0]) == 24
