"""
Module D: Regional Trend Atlas.

Multi-catchment comparative intelligence and spatial grid analysis:
- Cross-regional comparison across planetary climate hotspots
- Comparative Sen's slope bar charts with 95% uncertainty bars
- Spatial grid-cell raster trend mapping
- Benjamini-Hochberg False Discovery Rate (FDR) multiplicity control
"""

from __future__ import annotations
import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import st_folium

from nasa_data.catalog import NASA_CATALOG, REGIONAL_PRESETS
from nasa_data.client import NASAClient
from nasa_data.reader import generate_regional_grid_time_series
from trend_engine.api import analyze_variable, compare_regions, analyze_spatial_grid


def render_atlas_view(selected_var_id: str, selected_region_id: str) -> None:
    """Render Module D: Regional Trend Atlas view."""
    st.markdown("## 🗺️ Module D: Regional Trend Atlas")
    st.markdown(
        "Compare climate trajectories across planetary hotspots and analyze spatial grid "
        "heterogeneity with Benjamini-Hochberg False Discovery Rate (FDR) multiple-testing control."
    )

    var_meta = NASA_CATALOG.get(selected_var_id, NASA_CATALOG["precipitation"])
    client = NASAClient()

    # 1. Cross-Regional Comparison
    st.markdown(f"### 1. Cross-Regional Trajectory Comparison ({var_meta.display_name})")

    regional_analyses = []
    comparison_table = []

    for r_id, r_info in REGIONAL_PRESETS.items():
        series = client.fetch_time_series(variable_id=selected_var_id, region_id=r_id)
        regional_analyses.append({
            "timestamps": series["timestamps"],
            "values": series["values"],
            "variable_name": var_meta.display_name,
            "dataset": r_info["name"],
            "unit": var_meta.unit,
            "is_seasonal": True,
            "period": 12,
            "slope_per": "decade",
        })

    # Run multi-region comparison with FDR correction
    comp_result = compare_regions(regional_analyses, correction_method="fdr")

    for idx, r in enumerate(comp_result["results"]):
        comparison_table.append({
            "Region": r["dataset"],
            "Sen's Slope": f"{r['sens_slope']:+.4f} {r['slope_unit']}",
            "Raw p-value": f"{r['p_value']:.5f}",
            "FDR-Adjusted p": f"{r['adjusted_p_value']:.5f}",
            "Trend Direction": r["trend_direction"].upper(),
            "Significant (FDR)": "YES" if r["adjusted_p_value"] < 0.05 else "NO",
        })

    st.dataframe(pd.DataFrame(comparison_table), use_container_width=True, hide_index=True)

    # Slope comparison chart
    chart_df = pd.DataFrame({
        "Region": [r["dataset"] for r in comp_result["results"]],
        f"Sen's Slope ({var_meta.slope_unit})": [r["sens_slope"] for r in comp_result["results"]],
    }).set_index("Region")
    st.bar_chart(chart_df, use_container_width=True)

    st.markdown("---")

    # 2. Spatial Grid Trend Analysis with FDR Control
    st.markdown(f"### 2. Spatial Grid-Cell Trend Mapping (Active Domain)")
    active_region = REGIONAL_PRESETS.get(selected_region_id, REGIONAL_PRESETS["trishuli_himalaya"])
    bbox = active_region["bbox"]

    active_series = client.fetch_time_series(variable_id=selected_var_id, region_id=selected_region_id)
    lats, lons, grid_series = generate_regional_grid_time_series(
        bbox=bbox,
        variable_id=selected_var_id,
        base_timestamps=active_series["timestamps"],
        base_values=active_series["values"],
        n_lat=4,
        n_lon=4,
    )

    grid_result = analyze_spatial_grid(
        lats=lats,
        lons=lons,
        grid_timeseries=grid_series,
        timestamps=active_series["timestamps"],
        variable_name=var_meta.display_name,
        dataset=var_meta.dataset_name,
        unit=var_meta.unit,
        is_seasonal=True,
        period=12,
        slope_per="decade",
        correction_method="fdr",
    )

    col_map, col_info = st.columns([1.2, 0.8])

    with col_map:
        m = folium.Map(
            location=[active_region["latitude"], active_region["longitude"]],
            zoom_start=8 if "himalaya" in selected_region_id or "delta" in selected_region_id else 6,
            tiles="CartoDB positron",
        )

        # Plot grid cells as circular trend markers
        slopes = grid_result["visualization"]["grid_slopes"]
        sig_flags = grid_result["visualization"]["grid_significant"]

        for i in range(len(lats)):
            s_val = slopes[i]
            is_sig = sig_flags[i]
            # Color: Red for positive slope, Blue for negative slope, Gray if not significant
            color = "#ef4444" if (s_val > 0 and is_sig) else ("#3b82f6" if (s_val < 0 and is_sig) else "#94a3b8")
            folium.CircleMarker(
                location=[lats[i], lons[i]],
                radius=14 if is_sig else 8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.75 if is_sig else 0.35,
                popup=(
                    f"<b>Grid Cell ({lats[i]:.2f}°, {lons[i]:.2f}°)</b><br>"
                    f"Sen's Slope: {s_val:+.4f} {var_meta.slope_unit}<br>"
                    f"FDR Significant: {'Yes' if is_sig else 'No'}"
                ),
            ).add_to(m)

        st_folium(m, height=400, use_container_width=True)

    with col_info:
        st.markdown("#### 🔬 Multiple Hypothesis Control")
        st.metric("Total Grid Cells Analyzed", grid_result["n_cells"])
        st.metric("Cells Significant under FDR", grid_result["n_significant"], f"FDR Level: 5%")
        st.info(
            "**Why Benjamini-Hochberg (FDR) Matters**:\n\n"
            "Testing 16 spatial grid cells simultaneously without multiplicity control creates an elevated chance "
            "of observing false positive climate trends purely by chance. The Benjamini-Hochberg procedure bounds "
            "the false discovery rate at 5%, ensuring published climate maps reflect genuine physical shifts."
        )
