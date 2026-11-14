"""
Module E: Impact Intelligence & Disaster Triage.

Bridges multi-decadal Earth observation trends with ground-level disaster response:
- Climate Trend Impact Vulnerability Index (IVI) & return period scaling
- Tactical flood triage map with SAR, U-Net, DEM, and OSM infrastructure layers
- Cut-off settlement isolation ranking and walking escape route estimates
- Helicopter Landing Zone (HLZ) safety analysis
- Bilingual (English/Nepali) PDF SitRep generation and SMS broadcast transmission
"""

from __future__ import annotations
from pathlib import Path
import json
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

from trend_engine.models import TrendResult
from trend_engine.impact import assess_climate_trend_impact
try:
    from frontend.components import (
        load_run_from_folder,
        build_folium_map,
        render_kpi_row,
        render_priority_villages_table,
        render_tabs,
    )
except (ImportError, ModuleNotFoundError):
    from frontend.components import (
        load_run_from_folder,
        build_folium_map,
        render_kpi_row,
        render_priority_villages_table,
        render_tabs,
    )


def render_impact_view(trend_result: TrendResult, region_name: str, run_dir_str: str) -> None:
    """Render Module E: Impact Intelligence & Tactical Disaster Triage."""
    st.markdown("## 🚨 Module E: Impact Intelligence & Tactical Disaster Triage")
    st.markdown(
        "Bridge multi-decadal satellite trends with operational disaster response. "
        "Observe how long-term precipitation and warming trends directly amplify flash flood cut-offs, "
        "structural bridge inundation, and evacuation urgency."
    )

    # 1. Climate-to-Impact Vulnerability Scorecard
    st.markdown("### 1. Climate Trend Impact Coupling Assessment")

    # Load baseline triage metrics if available
    baseline_asset_summary = None
    try:
        run_data = load_run_from_folder(run_dir_str)
        baseline_asset_summary = run_data.get("summary", {})
    except Exception:
        pass

    impact = assess_climate_trend_impact(
        trend_result=trend_result,
        region_name=region_name,
        baseline_asset_summary=baseline_asset_summary,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Impact Vulnerability Index",
        f"{impact.impact_vulnerability_index:.1f} / 100",
        f"Category: {impact.impact_category}",
    )
    c2.metric(
        "50-Yr Extreme Shift",
        f"+{impact.extreme_event_frequency_shift_pct:.1f}%",
        "Hydrologic Scaling",
    )
    c3.metric(
        "Driver Trend",
        f"{impact.trend_slope:+.3f} {impact.slope_unit}",
        "Significant" if impact.is_statistically_significant else "Natural Variability",
    )
    c4.metric(
        "Statistical Confidence",
        impact.confidence_level,
        "Reproducible",
    )

    with st.expander("📌 Climate Trend Impact Implications & Tactical Engineering Directives", expanded=True):
        col_imp, col_rec = st.columns(2)
        with col_imp:
            st.markdown("#### ⚡ Physical Infrastructure Implications")
            for imp in impact.infrastructure_implications:
                st.markdown(f"- {imp}")
        with col_rec:
            st.markdown("#### 🛡️ Tactical Engineering & Defense Recommendations")
            for rec in impact.tactical_recommendations:
                st.markdown(f"- {rec}")

    st.markdown("---")

    # 2. Existing Tactical Disaster Triage Dashboard
    st.markdown("### 2. Tactical Disaster Response Engine (Trishuli Corridor Case Study)")

    if not Path(run_dir_str).exists():
        st.warning(f"Tactical run directory `{run_dir_str}` not found. Please verify local cache.")
        return

    try:
        data = load_run_from_folder(run_dir_str)
    except Exception as e:
        st.error(f"Error loading tactical disaster run: {e}")
        return

    summary = data.get("summary", {})
    damaged_bldgs = data.get("damaged_buildings", {})
    damaged_roads = data.get("damaged_roads", {})
    damaged_bridges = data.get("damaged_bridges", {})
    priorities = data.get("priorities", [])
    hlz_geojson = data.get("landing_zones_geojson", {})
    trace_coords = data.get("trace_coords", [])
    sms_text = data.get("sms_text", "")
    run_path = data.get("run_dir", run_dir_str)
    bbox = data.get("bbox", (85.20, 27.80, 85.45, 28.15))
    flood_date = data.get("flood_date", "2026-08-26")

    # Render KPI metrics row
    render_kpi_row(summary, 2)

    # Render Folium tactical map
    st.markdown("#### 🗺️ Multi-Layer Satellite Disaster Map")
    col_map, col_table = st.columns([1.3, 0.7])

    with col_map:
        m = build_folium_map(
            damaged_buildings=damaged_bldgs,
            damaged_roads=damaged_roads,
            damaged_bridges=damaged_bridges,
            landing_zones=hlz_geojson,
            trace_coords=trace_coords,
            bbox=bbox,
            class_map=data.get("class_map"),
            cant_see_mask=data.get("cant_see_mask"),
            show_water=True,
            show_debris=True,
            show_shadow=True,
            show_buildings=True,
            show_roads=True,
            show_bridges=True,
            show_hlz=True,
            show_flowpath=True,
        )
        st_folium(m, height=480, use_container_width=True)

    with col_table:
        render_priority_villages_table(priorities)

    # Detail tabs: Assets, HLZ, Flowpath, Reports
    render_tabs(
        damaged_buildings=damaged_bldgs,
        damaged_roads=damaged_roads,
        damaged_bridges=damaged_bridges,
        landing_zones=hlz_geojson,
        trace_coords=trace_coords,
        settlement_arrivals=[],
        sms_text=sms_text,
        run_dir=run_path,
        flood_date=flood_date,
        area_name="Bhote Koshi - Trishuli Corridor, Nepal",
    )
