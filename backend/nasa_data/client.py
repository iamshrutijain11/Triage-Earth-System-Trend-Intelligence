"""
NASA Earth Observation Client.

Connects to NASA POWER (Prediction Of Worldwide Energy Resources) REST API,
translates parameters, caches responses to local disk, and seamlessly falls back
to curated historical benchmark data if the remote endpoint is unreachable.
"""

from __future__ import annotations
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import requests

from nasa_data.catalog import NASA_CATALOG, REGIONAL_PRESETS, VariableMetadata
from nasa_data.local_store import get_curated_benchmark_series

logger = logging.getLogger(__name__)

NASA_POWER_ENDPOINT = "https://power.larc.nasa.gov/api/temporal/monthly/point"


class NASAClient:
    """Client for retrieving NASA Earth-science observations."""

    def __init__(self, cache_dir: Optional[str] = None, timeout: int = 8):
        self.cache_dir = Path(cache_dir or "data/cache/nasa")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

    def fetch_time_series(
        self,
        variable_id: str,
        region_id: str = "trishuli_himalaya",
        start_year: int = 1990,
        end_year: int = 2024,
        force_remote: bool = False,
    ) -> Dict[str, Any]:
        """Fetch monthly time series for a specified NASA variable and region.

        Parameters
        ----------
        variable_id : str
            Identifier in NASA_CATALOG (e.g. "precipitation", "temperature_2m").
        region_id : str
            Identifier in REGIONAL_PRESETS (e.g. "trishuli_himalaya").
        start_year : int
            Start year for multi-decadal analysis.
        end_year : int
            End year.
        force_remote : bool
            Whether to bypass local cache and force remote NASA query.

        Returns
        -------
        dict with timestamps, values, metadata, and provenance.
        """
        var_meta = NASA_CATALOG.get(variable_id)
        if not var_meta:
            raise ValueError(f"Unknown variable: {variable_id}. Valid: {list(NASA_CATALOG.keys())}")

        region_info = REGIONAL_PRESETS.get(region_id, REGIONAL_PRESETS["trishuli_himalaya"])
        lat = region_info["latitude"]
        lon = region_info["longitude"]

        cache_file = self.cache_dir / f"{variable_id}_{region_id}_{start_year}_{end_year}.json"

        # Check local cache first
        if not force_remote and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["timestamps"] = np.array(data["timestamps"], dtype=float)
                data["values"] = np.array(data["values"], dtype=float)
                return data
            except Exception as e:
                logger.warning(f"Failed to read cache {cache_file}: {e}")

        # Attempt remote query if NASA POWER parameter is defined
        if var_meta.nasa_power_param is not None:
            remote_data = self._query_nasa_power(
                param=var_meta.nasa_power_param,
                lat=lat,
                lon=lon,
                start_year=start_year,
                end_year=end_year,
                var_meta=var_meta,
                region_info=region_info,
            )
            if remote_data is not None:
                self._save_cache(cache_file, remote_data)
                return remote_data

        # Fall back to verified curated benchmark series
        logger.info(f"Using verified NASA benchmark dataset for {variable_id} at {region_id}")
        benchmark_data = get_curated_benchmark_series(
            variable_id=variable_id,
            region_id=region_id,
            start_year=start_year,
            end_year=end_year,
        )
        self._save_cache(cache_file, benchmark_data)
        return benchmark_data

    def _query_nasa_power(
        self,
        param: str,
        lat: float,
        lon: float,
        start_year: int,
        end_year: int,
        var_meta: VariableMetadata,
        region_info: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Query the NASA POWER monthly endpoint."""
        url = (
            f"{NASA_POWER_ENDPOINT}"
            f"?parameters={param}"
            f"&community=AG"
            f"&longitude={lon:.4f}"
            f"&latitude={lat:.4f}"
            f"&start={start_year}"
            f"&end={end_year}"
            f"&format=JSON"
        )
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                logger.warning(f"NASA POWER API returned HTTP {resp.status_code}")
                return None

            payload = resp.json()
            param_data = payload.get("properties", {}).get("parameter", {}).get(param, {})
            if not param_data:
                return None

            timestamps = []
            values = []
            # Keys in NASA POWER monthly are 'YYYYMM' or 'YYYY13' (annual mean)
            for y in range(start_year, end_year + 1):
                for m in range(1, 13):
                    key = f"{y}{m:02d}"
                    if key in param_data:
                        val = float(param_data[key])
                        # NASA POWER missing value sentinel is -999.0
                        if val == -999.0:
                            val = np.nan
                        timestamps.append(y + (m - 1) / 12.0)
                        values.append(val)

            if len(values) < 24:
                return None

            provenance = {
                "agency": "NASA Earth Science Division",
                "dataset": "NASA POWER MERRA-2 (v2.0)",
                "mission": "NASA Global Modeling and Assimilation Office (GMAO)",
                "spatial_resolution": "0.5° × 0.625°",
                "temporal_frequency": "Monthly",
                "retrieval_status": "REAL_NASA_API_OBSERVATION",
                "source_api": "https://power.larc.nasa.gov",
                "temporal_coverage": f"{start_year}-01 to {end_year}-12 ({len(values)} observations)",
            }

            return {
                "variable_id": var_meta.id,
                "variable_name": var_meta.display_name,
                "unit": var_meta.unit,
                "slope_unit": var_meta.slope_unit,
                "region_id": region_info["id"],
                "region_name": region_info["name"],
                "bbox": region_info["bbox"],
                "timestamps": np.array(timestamps, dtype=float),
                "values": np.array(values, dtype=float),
                "provenance": provenance,
            }

        except Exception as e:
            logger.warning(f"NASA POWER API request failed: {e}")
            return None

    def _save_cache(self, path: Path, data: Dict[str, Any]) -> None:
        """Save formatted series to disk."""
        try:
            serializable = dict(data)
            serializable["timestamps"] = list(data["timestamps"])
            serializable["values"] = [None if np.isnan(v) else float(v) for v in data["values"]]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache NASA dataset: {e}")
