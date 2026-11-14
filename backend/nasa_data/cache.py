"""
NASA Observation Cache Engine.

Provides persistent file-based caching for historical NASA Earth-science observations
with strict provenance enforcement: cached data is unambiguously marked as LOCAL_CACHE
and never masquerades as a live remote observation.
"""

from __future__ import annotations
import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

from nasa_data.schema import (
    ObservationRequest,
    NormalizedObservationSeries,
    GeoCoverage,
    MissingDataSummary,
    SourceProvenance,
    ObservationType,
    RetrievalStatus,
)


class ObservationCache:
    """Hash-verified local cache for NASA observation queries."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or "data/cache/nasa_observations")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_key(self, request: ObservationRequest) -> str:
        """Create a deterministic SHA-256 cache key from request parameters."""
        raw_key = (
            f"{request.dataset_id}::"
            f"{request.variable_id}::"
            f"{request.latitude:.4f}::"
            f"{request.longitude:.4f}::"
            f"{request.start_year}::"
            f"{request.end_year}::"
            f"{request.temporal_frequency}"
        )
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, request: ObservationRequest) -> Optional[NormalizedObservationSeries]:
        """Retrieve a cached observation series if it exists."""
        if request.bypass_cache:
            return None

        key = self._compute_key(request)
        cache_file = self.cache_dir / f"{key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct GeoCoverage
            geo_dict = data["geographical_coverage"]
            geo = GeoCoverage(
                latitude=float(geo_dict["latitude"]),
                longitude=float(geo_dict["longitude"]),
                region_id=geo_dict.get("region_id"),
                region_name=geo_dict.get("region_name"),
                bbox=tuple(geo_dict["bbox"]) if geo_dict.get("bbox") else None,
            )

            # Reconstruct MissingDataSummary
            mis_dict = data["missing_data_info"]
            missing_info = MissingDataSummary(
                total_observations=int(mis_dict["total_observations"]),
                missing_observations=int(mis_dict["missing_observations"]),
                valid_observations=int(mis_dict["valid_observations"]),
                missing_percentage=float(mis_dict["missing_percentage"]),
                max_consecutive_gap=int(mis_dict["max_consecutive_gap"]),
                gap_positions=mis_dict.get("gap_positions", []),
            )

            # Reconstruct SourceProvenance — strictly update retrieval_status to LOCAL_CACHE
            prov_dict = data["source_provenance"]
            prov = SourceProvenance(
                agency=prov_dict["agency"],
                dataset_name=prov_dict["dataset_name"],
                mission=prov_dict["mission"],
                observation_type=ObservationType(prov_dict["observation_type"]),
                processing_level=prov_dict["processing_level"],
                spatial_resolution=prov_dict["spatial_resolution"],
                temporal_resolution=prov_dict["temporal_resolution"],
                retrieval_status=RetrievalStatus.LOCAL_CACHE,  # Strict rule: mark as cached
                retrieval_timestamp=prov_dict["retrieval_timestamp"],
                source_url=prov_dict["source_url"],
                citation=prov_dict["citation"],
                license_info=prov_dict.get("license_info", "NASA Open Data Policy"),
            )

            # Reconstruct arrays (converting nulls back to np.nan)
            timestamps = np.array(data["timestamps"], dtype=float)
            vals_list = [np.nan if v is None else float(v) for v in data["values"]]
            values = np.array(vals_list, dtype=float)

            return NormalizedObservationSeries(
                dataset_id=data["dataset_id"],
                dataset_name=data["dataset_name"],
                variable_id=data["variable_id"],
                variable_name=data["variable_name"],
                unit=data["unit"],
                slope_unit=data["slope_unit"],
                geographical_coverage=geo,
                requested_period=data["requested_period"],
                actual_observation_period=data["actual_observation_period"],
                temporal_resolution=data["temporal_resolution"],
                timestamps=timestamps,
                values=values,
                missing_data_info=missing_info,
                source_provenance=prov,
                raw_metadata=data.get("raw_metadata", {}),
            )

        except Exception:
            return None

    def put(self, request: ObservationRequest, series: NormalizedObservationSeries) -> None:
        """Save a normalized series to cache."""
        try:
            key = self._compute_key(request)
            cache_file = self.cache_dir / f"{key}.json"
            data_dict = series.to_dict()
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=2)
        except Exception:
            pass
