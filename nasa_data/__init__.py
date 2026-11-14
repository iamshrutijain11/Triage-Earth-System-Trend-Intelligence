"""
NASA Earth Observation Data Module.

Provides access to real and curated NASA Earth-science datasets for trend analysis:
- Precipitation (GPM IMERG, MERRA-2)
- Surface Air Temperature (AIRS, MERRA-2)
- Soil Moisture (SMAP, MERRA-2)
- Vegetation Index (MODIS NDVI)
- Solar Irradiance & Energy Flux (CERES, NASA POWER)
"""

from nasa_data.catalog import NASA_CATALOG, VariableMetadata
from nasa_data.client import NASAClient
from nasa_data.local_store import get_curated_benchmark_series

__all__ = [
    "NASA_CATALOG",
    "VariableMetadata",
    "NASAClient",
    "get_curated_benchmark_series",
]
