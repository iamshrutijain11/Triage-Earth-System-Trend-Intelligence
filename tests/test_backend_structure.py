"""
Test suite validating the clean frontend/ and backend/ directory architecture.

Verifies:
1. Direct imports from backend (nasa_data, trend_engine, triage, shared)
2. Direct imports from frontend (app, components, views)
3. End-to-end importability of the clean architecture
"""

import pytest


def test_backend_top_level_imports():
    """Verify clean top-level imports from backend package."""
    import backend
    from backend import nasa_data
    from backend import trend_engine
    from backend import triage
    from backend import shared

    assert hasattr(backend, "nasa_data")
    assert hasattr(backend, "trend_engine")
    assert hasattr(backend, "triage")
    assert hasattr(backend, "shared")


def test_backend_triage_subpackages():
    """Verify unified backend.triage exports all domain capabilities."""
    from backend.triage import (
        fetch,
        detect,
        terrain,
        flowpath,
        rescue,
        damage,
        network,
        eval,
        report,
        run,
    )

    assert callable(run)
    assert hasattr(fetch, "fetch_s1")
    assert hasattr(detect, "fuse_detections")
    assert hasattr(rescue, "detect_landing_zones")
    assert hasattr(damage, "run_damage")


def test_backend_nasa_data_and_trend_engine():
    """Verify NASA data acquisition and trend engine under backend."""
    from backend.nasa_data import (
        get_available_datasets,
        get_available_variables,
        fetch_historical_data,
        check_data_source_health,
        ObservationRequest,
    )
    from backend.trend_engine import (
        TrendAnalyzer,
        analyze_variable,
        analyze_normalized_series,
        assess_climate_trend_impact,
    )

    datasets = get_available_datasets()
    assert len(datasets) >= 3

    analyzer = TrendAnalyzer()
    assert analyzer.alpha == 0.05


def test_frontend_presentation_tier():
    """Verify clean presentation tier under frontend package."""
    import frontend
    from frontend import app
    from frontend import components
    from frontend.views import (
        v_explorer,
        v_trend_lab,
        v_statistics,
        v_atlas,
        v_impact,
    )

    assert hasattr(app, "main")
    assert hasattr(components, "build_folium_map")
    assert hasattr(v_explorer, "render_explorer_view")
    assert hasattr(v_trend_lab, "render_trend_lab_view")
    assert hasattr(v_statistics, "render_statistics_view")
    assert hasattr(v_atlas, "render_atlas_view")
    assert hasattr(v_impact, "render_impact_view")


def test_scripts_cli_runner():
    """Verify scripts module exports case study runner."""
    import scripts
    from scripts import run_case_study

    assert hasattr(run_case_study, "main")
