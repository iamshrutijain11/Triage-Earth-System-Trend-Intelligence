"""
Public API Endpoints for NASA Earth-Science Data Acquisition.

Provides clean, typed interfaces for dataset discovery, variable inspection,
geographic region selection, historical observation retrieval, and system health checks.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
import logging

from nasa_data.schema import (
    ObservationRequest,
    NormalizedObservationSeries,
    DatasetMetadata,
    SourceHealth,
    RetrievalStatus,
)
from nasa_data.catalog import NASA_CATALOG, REGIONAL_PRESETS, VariableMetadata
from nasa_data.registry import GLOBAL_REGISTRY
from nasa_data.cache import ObservationCache

logger = logging.getLogger(__name__)

# Global cache instance
_OBSERVATION_CACHE = ObservationCache()


def get_available_datasets() -> List[DatasetMetadata]:
    """Retrieve metadata for all registered NASA Earth-science datasets."""
    return GLOBAL_REGISTRY.list_datasets()


def get_available_variables(dataset_id: Optional[str] = None) -> List[VariableMetadata]:
    """List available environmental variables, optionally filtered by dataset ID."""
    if dataset_id:
        driver = GLOBAL_REGISTRY.get_driver(dataset_id)
        return list(driver.get_supported_variables().values())
    return list(NASA_CATALOG.values())


def get_available_regions() -> List[Dict[str, Any]]:
    """List supported geographic target presets with coordinates and bounding boxes."""
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "country": r["country"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
            "bbox": r["bbox"],
            "description": r["description"],
        }
        for r in REGIONAL_PRESETS.values()
    ]


def get_dataset_metadata(dataset_id: str) -> DatasetMetadata:
    """Retrieve detailed specification and provenance for a given NASA dataset."""
    driver = GLOBAL_REGISTRY.get_driver(dataset_id)
    return driver.metadata


def fetch_historical_data(request: ObservationRequest) -> NormalizedObservationSeries:
    """Acquire genuine historical environmental observations from NASA sources.

    Checks local hash cache first; if not present or bypassed, queries the designated
    NASA driver and caches the normalized result.

    Parameters
    ----------
    request : ObservationRequest
        User query specifying dataset, variable, spatial coordinates, and date range.

    Returns
    -------
    NormalizedObservationSeries
        Clean NumPy array of observations with gap diagnostics and provenance.
    """
    request.validate()

    # 1. Check persistent cache
    if not request.bypass_cache:
        cached_series = _OBSERVATION_CACHE.get(request)
        if cached_series is not None:
            logger.info(
                f"Cache hit: {request.dataset_id}::{request.variable_id} "
                f"[{request.start_year}-{request.end_year}] (Status: LOCAL_CACHE)"
            )
            return cached_series

    # 2. Resolve target driver
    driver = GLOBAL_REGISTRY.get_driver(request.dataset_id)

    # 3. Execute data acquisition
    series = driver.fetch_data(request)

    # 4. Save to cache
    _OBSERVATION_CACHE.put(request, series)

    return series


def check_data_source_health(dataset_id: Optional[str] = None) -> List[SourceHealth]:
    """Probe upstream NASA API endpoints and report latency and availability."""
    if dataset_id:
        driver = GLOBAL_REGISTRY.get_driver(dataset_id)
        return [driver.check_health()]

    health_reports = []
    for driver in GLOBAL_REGISTRY.list_drivers():
        try:
            health_reports.append(driver.check_health())
        except Exception as e:
            from nasa_data.schema import HealthStatus
            from datetime import datetime, timezone
            health_reports.append(
                SourceHealth(
                    dataset_id=driver.dataset_id,
                    name=driver.metadata.name,
                    status=HealthStatus.UNAVAILABLE,
                    latency_ms=0.0,
                    last_checked=datetime.now(timezone.utc).isoformat(),
                    message=f"Health probe failed: {e}",
                )
            )
    return health_reports
