"""
NASA Earth Observation Data Schemas & Contracts.

Defines strongly typed, scientific data structures for observation requests,
normalized series responses, provenance tracking, and data source health.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import json
import numpy as np


class ObservationType(str, Enum):
    """Scientific nature of the measurement process."""
    SATELLITE_OBSERVATION = "SATELLITE_OBSERVATION"      # Direct or multi-satellite sensor measurement (e.g. GPM IMERG, MODIS)
    REANALYSIS_MODEL = "REANALYSIS_MODEL"                # Atmospheric reanalysis assimilation model (e.g. MERRA-2)
    LAND_SURFACE_MODEL = "LAND_SURFACE_MODEL"            # Land surface hydrology simulation model (e.g. GLDAS Noah/Catchment)
    ASSIMILATED_HYBRID = "ASSIMILATED_HYBRID"            # Combined satellite sounding + assimilation model (e.g. AIRS + GEOS)


class RetrievalStatus(str, Enum):
    """Provenance tracking for data retrieval origin."""
    LIVE_NASA_API = "LIVE_NASA_API"                      # Directly received from official remote NASA endpoint
    LOCAL_CACHE = "LOCAL_CACHE"                          # Retrieved from local hash-verified query cache
    OFFLINE_BENCHMARK = "OFFLINE_BENCHMARK"              # Retrieved from verified offline benchmark archive


class HealthStatus(str, Enum):
    """Operational health of an upstream NASA data source."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class GeoCoverage:
    """Geographical target coordinates and spatial extent."""
    latitude: float
    longitude: float
    region_id: Optional[str] = None
    region_name: Optional[str] = None
    bbox: Optional[Tuple[float, float, float, float]] = None  # (min_lon, min_lat, max_lon, max_lat)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "region_id": self.region_id,
            "region_name": self.region_name,
            "bbox": list(self.bbox) if self.bbox else None,
        }


@dataclass(frozen=True)
class MissingDataSummary:
    """Rigorous non-parametric missing-data accounting."""
    total_observations: int
    missing_observations: int
    valid_observations: int
    missing_percentage: float
    max_consecutive_gap: int
    gap_positions: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceProvenance:
    """NASA data origin, provider, scientific platform, and license."""
    agency: str
    dataset_name: str
    mission: str
    observation_type: ObservationType
    processing_level: str
    spatial_resolution: str
    temporal_resolution: str
    retrieval_status: RetrievalStatus
    retrieval_timestamp: str
    source_url: str
    citation: str
    license_info: str = "NASA Open Data Policy (Public Domain)"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["observation_type"] = self.observation_type.value
        d["retrieval_status"] = self.retrieval_status.value
        return d


@dataclass
class ObservationRequest:
    """Standardized user query for historical NASA observations."""
    dataset_id: str
    variable_id: str
    latitude: float
    longitude: float
    start_year: int
    end_year: int
    region_id: Optional[str] = None
    bbox: Optional[Tuple[float, float, float, float]] = None
    temporal_frequency: str = "monthly"
    bypass_cache: bool = False
    allow_fallback: bool = True

    def validate(self) -> None:
        """Validate parameter ranges and date bounds."""
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Latitude must be between -90 and 90, got {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Longitude must be between -180 and 180, got {self.longitude}")
        if self.start_year > self.end_year:
            raise ValueError(f"start_year ({self.start_year}) cannot be after end_year ({self.end_year})")
        if self.start_year < 1950:
            raise ValueError(f"start_year ({self.start_year}) exceeds earliest satellite era (1950)")
        if self.end_year > 2030:
            raise ValueError(f"end_year ({self.end_year}) is in the distant future")


@dataclass
class NormalizedObservationSeries:
    """Normalized, gap-analyzed, and provenance-tracked observation series."""
    dataset_id: str
    dataset_name: str
    variable_id: str
    variable_name: str
    unit: str
    slope_unit: str
    geographical_coverage: GeoCoverage
    requested_period: str
    actual_observation_period: str
    temporal_resolution: str
    timestamps: np.ndarray
    values: np.ndarray
    missing_data_info: MissingDataSummary
    source_provenance: SourceProvenance
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-friendly dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.dataset_name,
            "variable_id": self.variable_id,
            "variable_name": self.variable_name,
            "unit": self.unit,
            "slope_unit": self.slope_unit,
            "geographical_coverage": self.geographical_coverage.to_dict(),
            "requested_period": self.requested_period,
            "actual_observation_period": self.actual_observation_period,
            "temporal_resolution": self.temporal_resolution,
            "timestamps": self.timestamps.tolist(),
            "values": [None if np.isnan(v) else float(v) for v in self.values],
            "missing_data_info": self.missing_data_info.to_dict(),
            "source_provenance": self.source_provenance.to_dict(),
            "raw_metadata": self.raw_metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


@dataclass(frozen=True)
class DatasetMetadata:
    """Formal metadata specification for an integrated NASA dataset."""
    id: str
    name: str
    agency: str
    mission: str
    observation_type: ObservationType
    temporal_resolution: str
    spatial_resolution: str
    temporal_coverage_start: str
    temporal_coverage_end: str
    description: str
    supported_variables: List[str]
    documentation_url: str
    citation: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["observation_type"] = self.observation_type.value
        return d


@dataclass(frozen=True)
class SourceHealth:
    """Health check outcome for an upstream NASA data source."""
    dataset_id: str
    name: str
    status: HealthStatus
    latency_ms: float
    last_checked: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d
