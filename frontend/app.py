"""
TRIAGE — Earth System Trend Intelligence & Impact Explorer.

NASA Space Apps 2026: "Be An Earth System Trend Detective!"

Unified multi-module platform featuring:
- Module A: Earth Explorer
- Module B: Trend Laboratory
- Module C: Statistical Intelligence
- Module D: Regional Trend Atlas
- Module E: Impact Intelligence & Tactical Disaster Triage
"""

from __future__ import annotations
import sys
import os
from pathlib import Path
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import streamlit as st
from streamlit_folium import st_folium

# Ensure project root and package dirs are in sys.path
app_dir = Path(__file__).resolve().parent
repo_root = app_dir
for candidate in (app_dir, app_dir.parent, app_dir.parent.parent):
    if (candidate / "CONTRACT.md").exists() or (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
        repo_root = candidate
        break

for p in (str(repo_root), str(app_dir), str(repo_root / "p4_app"), str(repo_root / "app")):
    if p not in sys.path:
        sys.path.insert(0, p)

from nasa_data.catalog import NASA_CATALOG, REGIONAL_PRESETS
from nasa_data.client import NASAClient
from trend_engine.analyzer import TrendAnalyzer
from trend_engine.visualization import build_timeseries_chart_data
from trend_engine.classification import interpret_result

try:
    from frontend.views.v_explorer import render_explorer_view
    from frontend.views.v_trend_lab import render_trend_lab_view
    from frontend.views.v_statistics import render_statistics_view
    from frontend.views.v_atlas import render_atlas_view
    from frontend.views.v_impact import render_impact_view
    from frontend.components import render_footer
except (ImportError, ModuleNotFoundError):
    from p4_app.app.views.v_explorer import render_explorer_view
    from p4_app.app.views.v_trend_lab import render_trend_lab_view
    from p4_app.app.views.v_statistics import render_statistics_view
    from p4_app.app.views.v_atlas import render_atlas_view
    from p4_app.app.views.v_impact import render_impact_view
    from p4_app.app.components import render_footer

# Page configuration
st.set_page_config(
    page_title="TRIAGE | Earth System Trend Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _detect_cli_run_dir() -> Optional[str]:
    """Check CLI arguments or environment variables for a run folder."""
    env_dir = os.environ.get("TRIAGE_RUN_DIR")
    if env_dir and Path(env_dir).exists():
        return env_dir

    for idx, arg in enumerate(sys.argv):
        if arg in ("--run-dir", "-r") and idx + 1 < len(sys.argv):
            candidate = sys.argv[idx + 1]
            if Path(candidate).exists():
                return candidate
        if arg.startswith("--run-dir="):
            candidate = arg.split("=", 1)[1]
            if Path(candidate).exists():
                return candidate
        clean_arg = arg.rstrip("/\\")
        if (
            arg not in ("streamlit", "run")
            and not arg.endswith(".py")
            and Path(clean_arg).exists()
            and Path(clean_arg).is_dir()
        ):
            return clean_arg
    return None


def main() -> None:
    # -------------------------------------------------------------------------
    # 1. Sidebar Header & Navigation
    # -------------------------------------------------------------------------
    st.sidebar.title("🌍 TRIAGE")
    st.sidebar.caption("NASA Space Apps 2026: Be An Earth System Trend Detective!")
    st.sidebar.markdown("---")

    modules = [
        "Module A: Earth Explorer",
        "Module B: Trend Laboratory",
        "Module C: Statistical Intelligence",
        "Module D: Regional Trend Atlas",
        "Module E: Impact & Tactical Triage",
    ]

    # If CLI run directory was provided, default to Module E (Tactical Triage)
    cli_dir = _detect_cli_run_dir()
    default_module_idx = 4 if cli_dir else 1  # Default to Trend Lab or Triage

    selected_module = st.sidebar.radio(
        "Navigation",
        modules,
        index=default_module_idx,
    )

    st.sidebar.markdown("---")

    # -------------------------------------------------------------------------
    # 2. Global Parameter Controls
    # -------------------------------------------------------------------------
    st.sidebar.markdown("### 🛰️ NASA Observation Query")

    var_options = list(NASA_CATALOG.keys())
    var_labels = [f"{NASA_CATALOG[k].display_name} ({NASA_CATALOG[k].category})" for k in var_options]
    selected_var_idx = st.sidebar.selectbox(
        "Environmental Variable",
        range(len(var_options)),
        format_func=lambda i: var_labels[i],
        index=0,
    )
    selected_var_id = var_options[selected_var_idx]

    region_options = list(REGIONAL_PRESETS.keys())
    region_labels = [f"{REGIONAL_PRESETS[k]['name']}" for k in region_options]
    selected_region_idx = st.sidebar.selectbox(
        "Geographic Target",
        range(len(region_options)),
        format_func=lambda i: region_labels[i],
        index=0,
    )
    selected_region_id = region_options[selected_region_idx]

    # Time span
    st.sidebar.markdown("### ⏱️ Time Period")
    year_range = st.sidebar.slider("Observation Range", min_value=1980, max_value=2025, value=(1985, 2024))

    st.sidebar.markdown("---")
    st.sidebar.caption("Data Source: NASA Earth Observing System (GPM, AIRS, SMAP, MERRA-2)")

    # -------------------------------------------------------------------------
    # 3. Data Retrieval & Statistical Engine Computation
    # -------------------------------------------------------------------------
    client = NASAClient()
    series_data = client.fetch_time_series(
        variable_id=selected_var_id,
        region_id=selected_region_id,
        start_year=year_range[0],
        end_year=year_range[1],
    )

    timestamps = series_data["timestamps"]
    values = series_data["values"]
    var_meta = NASA_CATALOG[selected_var_id]

    analyzer = TrendAnalyzer(alpha=0.05)
    trend_result = analyzer.analyze(
        timestamps=timestamps,
        values=values,
        variable_name=var_meta.display_name,
        dataset=var_meta.dataset_name,
        unit=var_meta.unit,
        is_seasonal=True,
        period=12,
        slope_per="decade",
        observation_period=f"{year_range[0]}-01 to {year_range[1]}-12",
    )

    viz_data = build_timeseries_chart_data(timestamps, values, trend_result)

    interpretation = interpret_result(
        variable_name=trend_result.variable_name,
        trend_direction=trend_result.trend_direction,
        sens_slope=trend_result.sens_slope,
        slope_unit=trend_result.slope_unit,
        p_value=trend_result.p_value,
        alpha=trend_result.significance_threshold,
        ci_lower=trend_result.ci_lower,
        ci_upper=trend_result.ci_upper,
        missing_pct=trend_result.missing_data_pct,
        autocorrelation_corrected=bool(trend_result.autocorrelation_significant),
    )

    # Tactical triage run directory
    run_dir_str = cli_dir or "data/runs/trishuli_2026-08-26"
    if not Path(run_dir_str).exists():
        run_dir_str = "data/mock_run"

    # -------------------------------------------------------------------------
    # 4. View Routing
    # -------------------------------------------------------------------------
    if selected_module == "Module A: Earth Explorer":
        render_explorer_view(
            selected_var_id=selected_var_id,
            selected_region_id=selected_region_id,
        )

    elif selected_module == "Module B: Trend Laboratory":
        render_trend_lab_view(
            series_data=series_data,
            trend_result=trend_result,
            viz_data=viz_data,
        )

    elif selected_module == "Module C: Statistical Intelligence":
        render_statistics_view(
            trend_result=trend_result,
            interpretation_text=interpretation,
        )

    elif selected_module == "Module D: Regional Trend Atlas":
        render_atlas_view(
            selected_var_id=selected_var_id,
            selected_region_id=selected_region_id,
        )

    elif selected_module == "Module E: Impact & Tactical Triage":
        render_impact_view(
            trend_result=trend_result,
            region_name=REGIONAL_PRESETS[selected_region_id]["name"],
            run_dir_str=run_dir_str,
        )

    # Common footer
    render_footer()


if __name__ == "__main__":
    main()
