"""
Catalog of NASA Earth science observation datasets and variables.

Defines provenance, missions, physical measurement units, and temporal frequencies
for Earth system trend analysis.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class VariableMetadata:
    """Metadata describing a NASA Earth observation variable."""
    id: str
    display_name: str
    category: str
    dataset_name: str
    mission: str
    unit: str
    slope_unit: str
    temporal_frequency: str
    spatial_resolution: str
    description: str
    nasa_power_param: Optional[str] = None
    default_min: float = 0.0
    default_max: float = 100.0


NASA_CATALOG: Dict[str, VariableMetadata] = {
    "precipitation": VariableMetadata(
        id="precipitation",
        display_name="Precipitation Rate",
        category="Hydrosphere",
        dataset_name="GPM IMERG / MERRA-2",
        mission="Global Precipitation Measurement & Modern-Era Retrospective Analysis",
        unit="mm / month",
        slope_unit="mm / month / decade",
        temporal_frequency="Monthly",
        spatial_resolution="0.1° (~10 km) / 0.5°",
        description="Total corrected precipitation rate aggregated monthly from NASA GPM satellite microwave-infrared radar constellations and MERRA-2 assimilation.",
        nasa_power_param="PRECTOTCORR",
        default_min=0.0,
        default_max=800.0,
    ),
    "temperature_2m": VariableMetadata(
        id="temperature_2m",
        display_name="Surface Air Temperature (2m)",
        category="Atmosphere",
        dataset_name="AIRS / MERRA-2",
        mission="Atmospheric Infrared Sounder & MERRA-2",
        unit="°C",
        slope_unit="°C / decade",
        temporal_frequency="Monthly",
        spatial_resolution="0.5° × 0.625°",
        description="Monthly average 2-meter atmospheric surface temperature combining NASA AIRS soundings with Goddard Earth Observing System (GEOS) assimilation.",
        nasa_power_param="T2M",
        default_min=-30.0,
        default_max=45.0,
    ),
    "temperature_max": VariableMetadata(
        id="temperature_max",
        display_name="Maximum Air Temperature (2m)",
        category="Atmosphere",
        dataset_name="MERRA-2 Climatology",
        mission="Modern-Era Retrospective Analysis for Research and Applications",
        unit="°C",
        slope_unit="°C / decade",
        temporal_frequency="Monthly",
        spatial_resolution="0.5° × 0.625°",
        description="Monthly maximum 2-meter air temperature capturing seasonal heatwave amplitude and extreme temperature shifts.",
        nasa_power_param="T2M_MAX",
        default_min=-25.0,
        default_max=50.0,
    ),
    "soil_moisture": VariableMetadata(
        id="soil_moisture",
        display_name="Root-Zone Soil Wetness",
        category="Hydrosphere",
        dataset_name="SMAP / MERRA-2",
        mission="Soil Moisture Active Passive",
        unit="Index (0-1)",
        slope_unit="Fraction / decade",
        temporal_frequency="Monthly",
        spatial_resolution="9 km / 0.5°",
        description="Top-layer root zone soil moisture content index derived from SMAP L-band radiometry and catchment land-surface modeling.",
        nasa_power_param="GWETTOP",
        default_min=0.0,
        default_max=1.0,
    ),
    "ndvi": VariableMetadata(
        id="ndvi",
        display_name="Normalized Difference Vegetation Index (NDVI)",
        category="Biosphere",
        dataset_name="MODIS Terra/Aqua MOD13A2",
        mission="Moderate Resolution Imaging Spectroradiometer (Terra/Aqua)",
        unit="NDVI Index",
        slope_unit="NDVI / decade",
        temporal_frequency="Monthly",
        spatial_resolution="1 km",
        description="Vegetation canopy greenness and photosynthetic activity derived from MODIS red and near-infrared reflectance.",
        nasa_power_param=None,
        default_min=0.0,
        default_max=1.0,
    ),
    "solar_radiation": VariableMetadata(
        id="solar_radiation",
        display_name="All-Sky Surface Solar Insolation",
        category="Energy Budget",
        dataset_name="CERES / NASA POWER",
        mission="Clouds and the Earth's Radiant Energy System",
        unit="MJ/m² / day",
        slope_unit="MJ/m² / day / decade",
        temporal_frequency="Monthly",
        spatial_resolution="1.0°",
        description="Monthly surface downward shortwave radiation flux measuring incident solar energy at the Earth's surface.",
        nasa_power_param="ALLSKY_SFC_SW_DWN",
        default_min=0.0,
        default_max=35.0,
    ),
}


REGIONAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "trishuli_himalaya": {
        "id": "trishuli_himalaya",
        "name": "Hindu Kush-Himalaya (Bhote Koshi / Trishuli Basin)",
        "country": "Nepal",
        "latitude": 27.95,
        "longitude": 85.32,
        "bbox": [85.10, 27.75, 85.55, 28.25],
        "description": "High-altitude glacial, mountainous river corridor susceptible to rapid monsoon warming, glacier lake outburst floods (GLOF), and extreme monsoonal precipitation.",
    },
    "mekong_delta": {
        "id": "mekong_delta",
        "name": "Lower Mekong River Basin",
        "country": "Vietnam / Cambodia",
        "latitude": 10.50,
        "longitude": 105.50,
        "bbox": [104.50, 9.50, 106.50, 11.50],
        "description": "Dense agricultural delta critical for rice production, vulnerable to upstream hydrological shifts, salinization, and prolonged tropical dry seasons.",
    },
    "colorado_basin": {
        "id": "colorado_basin",
        "name": "Upper Colorado River Basin",
        "country": "United States",
        "latitude": 39.50,
        "longitude": -107.50,
        "bbox": [-109.50, 38.00, -105.50, 41.00],
        "description": "Arid mountainous basin providing municipal and agricultural water to 40M people, experiencing multi-decadal aridification and declining snowpack.",
    },
    "horn_of_africa": {
        "id": "horn_of_africa",
        "name": "Horn of Africa Drylands",
        "country": "Kenya / Ethiopia / Somalia",
        "latitude": 4.50,
        "longitude": 40.50,
        "bbox": [37.50, 2.00, 43.50, 7.00],
        "description": "Semi-arid rangelands vulnerable to recurring consecutive drought cycles, bimodal rainy season failures, and intense heat anomalies.",
    },
}
