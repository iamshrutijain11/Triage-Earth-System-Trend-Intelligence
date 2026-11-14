"""
Base Abstract Class for NASA Data Source Drivers.

Enforces standardized request validation, unit lockdown, missing-data computation,
and provenance tracking across all NASA Earth observation integrations.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import numpy as np

from nasa_data.schema import (
    ObservationRequest,
    NormalizedObservationSeries,
    DatasetMetadata,
    SourceHealth,
    MissingDataSummary,
    SourceProvenance,
    GeoCoverage,
    ObservationType,
    RetrievalStatus,
    HealthStatus,
)
from nasa_data.catalog import VariableMetadata


class BaseNASADataSource(ABC):
    """Abstract Base Class for a NASA data source driver."""

    def __init__(self, metadata: DatasetMetadata):
        self.metadata = metadata

    @property
    def dataset_id(self) -> str:
        return self.metadata.id

    @abstractmethod
    def get_supported_variables(self) -> Dict[str, VariableMetadata]:
        """Return a mapping of variable_id -> VariableMetadata supported by this source."""
        pass

    def validate_request(self, request: ObservationRequest) -> None:
        """Validate request against official dataset parameters and capabilities."""
        request.validate()
        supported = self.get_supported_variables()
        if request.variable_id not in supported:
            valid_list = list(supported.keys())
            raise ValueError(
                f"Variable '{request.variable_id}' is not supported by dataset '{self.dataset_id}'. "
                f"Supported variables: {valid_list}"
            )

    @abstractmethod
    def fetch_data(self, request: ObservationRequest) -> NormalizedObservationSeries:
        """Retrieve and normalize observations for the given request."""
        pass

    @abstractmethod
    def check_health(self) -> SourceHealth:
        """Check operational availability and latency of the upstream source."""
        pass

    @staticmethod
    def calculate_missing_data_summary(values: np.ndarray) -> MissingDataSummary:
        """Compute strict non-parametric missing-data accounting.
        NEVER invents or fills missing observations silently.
        """
        values = np.asarray(values, dtype=float)
        is_nan = np.isnan(values)
        n_total = len(values)
        n_missing = int(np.sum(is_nan))
        n_valid = n_total - n_missing
        pct_missing = (n_missing / n_total * 100.0) if n_total > 0 else 0.0

        max_gap = 0
        current_gap = 0
        gap_starts = []
        for i, flag in enumerate(is_nan):
            if flag:
                if current_gap == 0:
                    gap_starts.append(i)
                current_gap += 1
                max_gap = max(max_gap, current_gap)
            else:
                current_gap = 0

        return MissingDataSummary(
            total_observations=n_total,
            missing_observations=n_missing,
            valid_observations=n_valid,
            missing_percentage=round(pct_missing, 2),
            max_consecutive_gap=max_gap,
            gap_positions=gap_starts,
        )
