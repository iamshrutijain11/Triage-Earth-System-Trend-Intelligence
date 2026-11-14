"""
NASA Data Source Registry.

Central registry managing modular NASA data drivers, resolving dataset providers,
and enabling runtime extension with zero architectural refactoring.
"""

from __future__ import annotations
from typing import Dict, List, Optional
import logging

from nasa_data.drivers.base import BaseNASADataSource
from nasa_data.drivers.power import NASAPowerDriver
from nasa_data.drivers.gpm_imerg import NASAGPMIMERGDriver
from nasa_data.drivers.gldas import NASAGLDASDriver
from nasa_data.schema import DatasetMetadata

logger = logging.getLogger(__name__)


class DataSourceRegistry:
    """Registry maintaining active NASA data source drivers."""

    def __init__(self):
        self._drivers: Dict[str, BaseNASADataSource] = {}
        # Register default official drivers
        self.register(NASAPowerDriver())
        self.register(NASAGPMIMERGDriver())
        self.register(NASAGLDASDriver())

    def register(self, driver: BaseNASADataSource) -> None:
        """Register a new NASA data source driver."""
        self._drivers[driver.dataset_id] = driver
        logger.info(f"Registered NASA data source driver: {driver.dataset_id} ({driver.metadata.name})")

    def get_driver(self, dataset_id: str) -> BaseNASADataSource:
        """Retrieve driver by unique dataset ID."""
        if dataset_id not in self._drivers:
            available = list(self._drivers.keys())
            raise KeyError(f"Dataset '{dataset_id}' not found. Available datasets: {available}")
        return self._drivers[dataset_id]

    def resolve_driver_for_variable(self, variable_id: str, preferred_dataset_id: Optional[str] = None) -> BaseNASADataSource:
        """Select appropriate driver for a given variable with optional preference."""
        if preferred_dataset_id and preferred_dataset_id in self._drivers:
            driver = self._drivers[preferred_dataset_id]
            if variable_id in driver.get_supported_variables():
                return driver

        # Fallback to first driver supporting this variable
        for d in self._drivers.values():
            if variable_id in d.get_supported_variables():
                return d

        raise ValueError(f"No registered NASA driver supports variable '{variable_id}'.")

    def list_datasets(self) -> List[DatasetMetadata]:
        """List metadata for all registered NASA datasets."""
        return [driver.metadata for driver in self._drivers.values()]

    def list_drivers(self) -> List[BaseNASADataSource]:
        """Return list of active driver instances."""
        return list(self._drivers.values())


# Global singleton registry
GLOBAL_REGISTRY = DataSourceRegistry()
