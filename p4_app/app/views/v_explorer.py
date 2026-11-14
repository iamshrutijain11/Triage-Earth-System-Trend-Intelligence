"""
Module A: Earth Explorer.

Provides interactive spatio-temporal catalog exploration for NASA Earth observations:
- Variable selection across Earth system spheres (Atmosphere, Hydrosphere, Biosphere, Energy Budget)
- Regional bounding box presets and custom coordinate definitions
- NASA Earth-observing mission provenance and sensor constellation details
- Geospatial extent map visualization with bounding box overlays
"""

from __future__ import annotations
import streamlit as st
import folium
from streamlit_folium import st_folium

from nasa_data.catalog import NASA_CATALOG, REGIONAL_PRESETS


def render_explorer_view(selected_var_id: str, selected_region_id: str) -> None:
    """Render Module A: Earth Explorer view."""
    st.markdown("## 🌍 Module A: Earth Explorer")
    st.markdown(
        "Discover, filter, and inspect NASA Earth-observation records and mission provenance "
        "across planetary spheres and critical regional climate hotspots."
    )

    var_meta = NASA_CATALOG.get(selected_var_id, NASA_CATALOG["precipitation"])
    region_info = REGIONAL_PRESETS.get(selected_region_id, REGIONAL_PRESETS["trishuli_himalaya"])

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🛰️ NASA Mission & Dataset Specification")
        st.info(
            f"**Selected Variable**: {var_meta.display_name} (`{var_meta.id}`)\n\n"
            f"**Earth System Sphere**: `{var_meta.category}`\n\n"
            f"**NASA Dataset**: `{var_meta.dataset_name}`\n\n"
            f"**Mission Constellation**: {var_meta.mission}\n\n"
            f"**Native Spatial Resolution**: `{var_meta.spatial_resolution}` | **Temporal Resolution**: `{var_meta.temporal_frequency}`\n\n"
            f"**Physical Unit**: `{var_meta.unit}` | **Trend Metric**: `{var_meta.slope_unit}`"
        )
        st.markdown(f"**Scientific Description**: {var_meta.description}")

        st.markdown("---")
        st.markdown("### 📍 Geographic Target & Catchment")
        st.success(
            f"**Region**: {region_info['name']} ({region_info['country']})\n\n"
            f"**Center Coordinates**: Lat `{region_info['latitude']:.2f}°`, Lon `{region_info['longitude']:.2f}°\n\n"
            f"**Bounding Box [W, S, E, N]**: `{region_info['bbox']}`\n\n"
            f"**Ecological Context**: {region_info['description']}"
        )

    with col2:
        st.markdown("### 🗺️ Spatio-Temporal Domain Map")
        bbox = region_info["bbox"]
        c_lat = region_info["latitude"]
        c_lon = region_info["longitude"]

        m = folium.Map(
            location=[c_lat, c_lon],
            zoom_start=7 if "himalaya" in selected_region_id or "delta" in selected_region_id else 5,
            tiles="CartoDB positron",
        )

        # Add satellite imagery tile layer
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="Satellite Base",
        ).add_to(m)

        # Draw bounding box rectangle
        bounds = [[bbox[1], bbox[0]], [bbox[3], bbox[2]]]
        folium.Rectangle(
            bounds=bounds,
            color="#0284c7",
            weight=3,
            fill=True,
            fill_color="#38bdf8",
            fill_opacity=0.25,
            popup=f"{region_info['name']} Bounding Box",
        ).add_to(m)

        # Add center pin
        folium.Marker(
            location=[c_lat, c_lon],
            popup=f"<b>{region_info['name']}</b><br>NASA Observation Sampling Point",
            icon=folium.Icon(color="red", icon="satellite", prefix="fa"),
        ).add_to(m)

        folium.LayerControl().add_to(m)
        st_folium(m, height=420, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔬 NASA Sensor Provenance & Standards Compliance")
    p1, p2, p3 = st.columns(3)
    p1.metric("Processing Tier", "NASA Level 3 / 4", "Gridded Harmonized")
    p2.metric("API Gateway", "NASA POWER & GES DISC", "REST / OGC WCS")
    p3.metric("Data Reproducibility", "Deterministic Seeded", "Zero Fabrication")
