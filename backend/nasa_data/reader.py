"""
Data converters and raster grid formatters for NASA datasets.

Converts multi-dimensional spatial arrays into formats consumed by
the trend engine's spatial analysis and mapping pipelines.
"""

from __future__ import annotations
import numpy as np
from typing import List, Tuple, Dict, Any


def create_spatial_grid_from_bbox(
    bbox: Tuple[float, float, float, float],
    n_lat: int = 5,
    n_lon: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate uniform lat/lon coordinate arrays for a bounding box."""
    min_lon, min_lat, max_lon, max_lat = bbox
    lats = np.linspace(min_lat, max_lat, n_lat)
    lons = np.linspace(min_lon, max_lon, n_lon)
    return lats, lons


def generate_regional_grid_time_series(
    bbox: Tuple[float, float, float, float],
    variable_id: str,
    base_timestamps: np.ndarray,
    base_values: np.ndarray,
    n_lat: int = 4,
    n_lon: int = 4,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray, List[np.ndarray]]:
    """Synthesize spatial grid time series with realistic geographic gradients
    anchored to the regional benchmark series.

    Returns
    -------
    lats : 1D array of cell latitudes
    lons : 1D array of cell longitudes
    grid_series : list of 1D value arrays (one per grid cell)
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    lat_grid = np.linspace(min_lat, max_lat, n_lat)
    lon_grid = np.linspace(min_lon, max_lon, n_lon)

    rng = np.random.default_rng(seed)
    n_obs = len(base_values)

    all_lats = []
    all_lons = []
    grid_series = []

    # Calculate spatial center
    c_lat = (min_lat + max_lat) / 2.0
    c_lon = (min_lon + max_lon) / 2.0

    for i, lat in enumerate(lat_grid):
        for j, lon in enumerate(lon_grid):
            # Spatial gradient: orographic/latitudinal perturbation
            dist_lat = (lat - c_lat) / (max_lat - min_lat + 1e-5)
            dist_lon = (lon - c_lon) / (max_lon - min_lon + 1e-5)

            # E.g. temperature drops with latitude/elevation; precipitation varies with aspect
            spatial_scale = 1.0 + 0.15 * dist_lat - 0.10 * dist_lon
            local_noise = rng.normal(0, 0.05 * np.nanstd(base_values), size=n_obs)

            cell_values = base_values * spatial_scale + local_noise

            all_lats.append(lat)
            all_lons.append(lon)
            grid_series.append(cell_values)

    return np.array(all_lats), np.array(all_lons), grid_series
