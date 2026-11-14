"""
NASA Earth Observation Data Module.

Provides modular, provenance-tracked access to NASA Earth-science observation systems:
- NASA POWER API (MERRA-2 atmospheric assimilation & CERES solar insolation)
- NASA GPM IMERG (Global multi-satellite precipitation constellation)
- NASA GLDAS (Noah/Catchment land surface hydrology model)

Adheres strictly to NASA Open Data Policy standards:
- Explicit distinction between satellite observations and reanalysis models
- Missing values (-999.0 sentinels) preserved as NaNs without silent imputation
- Strict provenance tracking and local query caching
"""

from nasa_data.catalog import NASA_CATALOG, REGIONAL_PRESETS, VariableMetadata
from nasa_data.client import NASAClient
from nasa_data.schema import (
    ObservationRequest,
    NormalizedObservationSeries,
    DatasetMetadata,
    SourceHealth,
    GeoCoverage,
    MissingDataSummary,
    SourceProvenance,
    ObservationType,
    RetrievalStatus,
    HealthStatus,
)
from nasa_data.api import (
    get_available_datasets,
    get_available_variables,
    get_available_regions,
    get_dataset_metadata,
    fetch_historical_data,
    check_data_source_health,
)

__all__ = [
    # Catalog & Metadata
    "NASA_CATALOG",
    "REGIONAL_PRESETS",
    "VariableMetadata",
    "DatasetMetadata",
    "SourceHealth",
    "GeoCoverage",
    "MissingDataSummary",
    "SourceProvenance",
    "ObservationType",
    "RetrievalStatus",
    "HealthStatus",
    # Request & Response Contracts
    "ObservationRequest",
    "NormalizedObservationSeries",
    # Public API Endpoints
    "get_available_datasets",
    "get_available_variables",
    "get_available_regions",
    "get_dataset_metadata",
    "fetch_historical_data",
    "check_data_source_health",
    # Legacy client compatibility
    "NASAClient",
]
