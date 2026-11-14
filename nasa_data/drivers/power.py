"""
NASA POWER (Prediction Of Worldwide Energy Resources) Data Source Driver.

Implements official NASA POWER REST API integration for monthly climatological data:
- GMAO MERRA-2 atmospheric assimilation (Precipitation, 2m Air Temp, Soil Wetness)
- CERES satellite solar radiant flux
Strictly maps -999.0 sentinels to NaN, computes missing-data profiles, and tags provenance.
"""

from __future__ import annotations
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import requests

from nasa_data.drivers.base import BaseNASADataSource
from nasa_data.schema import (
    ObservationRequest,
    NormalizedObservationSeries,
    DatasetMetadata,
    SourceHealth,
    SourceProvenance,
    GeoCoverage,
    ObservationType,
    RetrievalStatus,
    HealthStatus,
)
from nasa_data.catalog import VariableMetadata, NASA_CATALOG, REGIONAL_PRESETS
from nasa_data.local_store import get_curated_benchmark_series

logger = logging.getLogger(__name__)

NASA_POWER_API_BASE = "https://power.larc.nasa.gov/api"
NASA_POWER_MONTHLY_POINT = f"{NASA_POWER_API_BASE}/temporal/monthly/point"
NASA_POWER_VERSION_URL = f"{NASA_POWER_API_BASE}/system/manager/version"


class NASAPowerDriver(BaseNASADataSource):
    """Driver for the NASA POWER API (MERRA-2 & CERES)."""

    def __init__(self, timeout: int = 10):
        metadata = DatasetMetadata(
            id="nasa_power",
            name="NASA POWER Climatology (MERRA-2 & CERES)",
            agency="NASA Earth Science Division",
            mission="NASA Applied Sciences / GMAO MERRA-2 & CERES",
            observation_type=ObservationType.REANALYSIS_MODEL,
            temporal_resolution="Monthly",
            spatial_resolution="0.5° × 0.625°",
            temporal_coverage_start="1981-01",
            temporal_coverage_end="2024-12",
            description=(
                "NASA Prediction Of Worldwide Energy Resources (POWER) monthly meteorological "
                "and solar energy data assimilated from GMAO MERRA-2 and CERES satellite instruments."
            ),
            supported_variables=["precipitation", "temperature_2m", "temperature_max", "soil_moisture", "solar_radiation"],
            documentation_url="https://power.larc.nasa.gov/docs/services/api/temporal/monthly/",
            citation="NASA POWER Project (2024), NASA Langley Research Center / GMAO MERRA-2.",
        )
        super().__init__(metadata)
        self.timeout = timeout

    def get_supported_variables(self) -> Dict[str, VariableMetadata]:
        return {
            vid: NASA_CATALOG[vid]
            for vid in self.metadata.supported_variables
            if vid in NASA_CATALOG
        }

    def fetch_data(self, request: ObservationRequest) -> NormalizedObservationSeries:
        """Fetch monthly observations from NASA POWER."""
        self.validate_request(request)
        var_meta = NASA_CATALOG[request.variable_id]
        power_param = var_meta.nasa_power_param

        if not power_param:
            raise ValueError(f"Variable '{request.variable_id}' lacks a defined NASA POWER parameter code.")

        # Determine observation type based on variable: CERES solar radiation is satellite observation
        obs_type = (
            ObservationType.SATELLITE_OBSERVATION
            if request.variable_id == "solar_radiation"
            else ObservationType.REANALYSIS_MODEL
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        # Query remote NASA POWER API
        url = (
            f"{NASA_POWER_MONTHLY_POINT}"
            f"?parameters={power_param}"
            f"&community=AG"
            f"&longitude={request.longitude:.4f}"
            f"&latitude={request.latitude:.4f}"
            f"&start={request.start_year}"
            f"&end={request.end_year}"
            f"&format=JSON"
        )

        logger.info(
            f"Querying NASA POWER endpoint for {request.variable_id} at "
            f"lat={request.latitude:.2f}, lon={request.longitude:.2f} [{request.start_year}-{request.end_year}]"
        )

        timestamps = []
        values = []
        is_live = False
        raw_meta = {}

        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200:
                payload = resp.json()
                raw_meta = payload.get("header", {})
                param_data = payload.get("properties", {}).get("parameter", {}).get(power_param, {})

                if param_data:
                    for y in range(request.start_year, request.end_year + 1):
                        for m in range(1, 13):
                            key = f"{y}{m:02d}"
                            if key in param_data:
                                val = float(param_data[key])
                                # Strictly map NASA POWER missing value sentinel -999.0 to np.nan
                                if val == -999.0:
                                    val = np.nan
                                timestamps.append(y + (m - 1) / 12.0)
                                values.append(val)

                    if len(values) >= 12:
                        is_live = True

            elif resp.status_code == 429:
                logger.warning("NASA POWER API rate limit encountered (HTTP 429).")
            else:
                logger.warning(f"NASA POWER API returned HTTP {resp.status_code}.")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error querying NASA POWER API: {e}")

        # If live retrieval failed, evaluate fallback
        if not is_live:
            if not request.allow_fallback:
                raise ConnectionError(
                    f"Failed to retrieve live observations from NASA POWER for {request.variable_id} "
                    f"and fallback is disabled."
                )

            logger.info(f"Using verified NASA benchmark dataset for {request.variable_id} (fallback mode)")
            region_key = request.region_id or "trishuli_himalaya"
            benchmark = get_curated_benchmark_series(
                variable_id=request.variable_id,
                region_id=region_key,
                start_year=request.start_year,
                end_year=request.end_year,
            )
            timestamps = benchmark["timestamps"].tolist()
            values = benchmark["values"].tolist()
            retrieval_status = RetrievalStatus.OFFLINE_BENCHMARK
        else:
            retrieval_status = RetrievalStatus.LIVE_NASA_API

        timestamps_arr = np.array(timestamps, dtype=float)
        values_arr = np.array(values, dtype=float)

        missing_info = self.calculate_missing_data_summary(values_arr)

        geo = GeoCoverage(
            latitude=request.latitude,
            longitude=request.longitude,
            region_id=request.region_id,
            region_name=request.region_id.replace("_", " ").title() if request.region_id else None,
            bbox=request.bbox,
        )

        provenance = SourceProvenance(
            agency="NASA Earth Science Division",
            dataset_name=self.metadata.name,
            mission=var_meta.mission,
            observation_type=obs_type,
            processing_level="Level 3 / Level 4 Gridded Assimilation",
            spatial_resolution=self.metadata.spatial_resolution,
            temporal_resolution=self.metadata.temporal_resolution,
            retrieval_status=retrieval_status,
            retrieval_timestamp=now_iso,
            source_url="https://power.larc.nasa.gov",
            citation=self.metadata.citation,
        )

        return NormalizedObservationSeries(
            dataset_id=self.dataset_id,
            dataset_name=self.metadata.name,
            variable_id=request.variable_id,
            variable_name=var_meta.display_name,
            unit=var_meta.unit,
            slope_unit=var_meta.slope_unit,
            geographical_coverage=geo,
            requested_period=f"{request.start_year}-01 to {request.end_year}-12",
            actual_observation_period=f"{int(timestamps_arr[0])}-01 to {int(timestamps_arr[-1])}-12",
            temporal_resolution="Monthly",
            timestamps=timestamps_arr,
            values=values_arr,
            missing_data_info=missing_info,
            source_provenance=provenance,
            raw_metadata=raw_meta,
        )

    def check_health(self) -> SourceHealth:
        """Ping NASA POWER system manager version endpoint to report operational status."""
        start_time = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            resp = requests.get(NASA_POWER_VERSION_URL, timeout=4)
            latency = (time.time() - start_time) * 1000.0
            if resp.status_code == 200:
                payload = resp.json()
                v_str = payload.get("version", "Active")
                return SourceHealth(
                    dataset_id=self.dataset_id,
                    name=self.metadata.name,
                    status=HealthStatus.HEALTHY,
                    latency_ms=round(latency, 1),
                    last_checked=now_iso,
                    message=f"NASA POWER API Operational (Version: {v_str})",
                )
            else:
                return SourceHealth(
                    dataset_id=self.dataset_id,
                    name=self.metadata.name,
                    status=HealthStatus.DEGRADED,
                    latency_ms=round(latency, 1),
                    last_checked=now_iso,
                    message=f"NASA POWER returned HTTP {resp.status_code}",
                )
        except Exception as e:
            latency = (time.time() - start_time) * 1000.0
            return SourceHealth(
                dataset_id=self.dataset_id,
                name=self.metadata.name,
                status=HealthStatus.UNAVAILABLE,
                latency_ms=round(latency, 1),
                last_checked=now_iso,
                message=f"Upstream NASA POWER API unreachable: {e}",
            )
