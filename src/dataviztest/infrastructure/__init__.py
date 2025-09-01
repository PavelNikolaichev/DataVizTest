"""Infrastructure layer for DataVizTest application.

This package contains cross-cutting concerns like configuration,
logging, caching, and exception handling.
"""

from .config import Settings, get_settings, update_settings, is_jupyter_environment, is_colab_environment
from .exceptions import (
    DataVizTestException,
    DataProcessingError,
    DataValidationError,
    FilterError,
    InvalidFilterError,
    FilterApplicationError,
    VisualizationError,
    PlotConfigurationError,
    RenderingError,
    GeospatialError,
    GeocodingError,
    MappingError,
    UIError,
    WidgetError,
    StateError,
    ConfigurationError,
    ExportError,
    CacheError,
    EnvironmentError,
    ErrorContext,
    handle_errors,
)
from .logging_config import setup_logging, get_logger, log_performance

__all__ = [
    # Configuration
    "Settings",
    "get_settings",
    "update_settings",
    "is_jupyter_environment",
    "is_colab_environment",
    
    # Exceptions
    "DataVizTestException",
    "DataProcessingError",
    "DataValidationError",
    "FilterError",
    "InvalidFilterError",
    "FilterApplicationError",
    "VisualizationError",
    "PlotConfigurationError",
    "RenderingError",
    "GeospatialError",
    "GeocodingError",
    "MappingError",
    "UIError",
    "WidgetError",
    "StateError",
    "ConfigurationError",
    "ExportError",
    "CacheError",
    "EnvironmentError",
    "ErrorContext",
    "handle_errors",
    
    # Logging
    "setup_logging",
    "get_logger",
    "log_performance",
]