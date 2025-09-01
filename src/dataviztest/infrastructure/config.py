"""Configuration management for DataVizTest application.

This module provides centralized configuration management with environment detection
and validation using Pydantic settings.
"""

from __future__ import annotations

import os
from typing import List, Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


def detect_environment() -> str:
    """Detect the current execution environment.
    
    Returns:
        Environment type: 'colab', 'jupyter', or 'standalone'
    """
    try:
        import google.colab  # noqa: F401
        return "colab"
    except ImportError:
        pass
    
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            return "jupyter"
    except ImportError:
        pass
    
    return "standalone"


class Settings(BaseSettings):
    """Application settings with environment-specific configuration."""
    
    # Application metadata
    app_name: str = Field(default="DataVizTest", description="Application name")
    version: str = Field(default="2.0.0", description="Application version")
    
    # Environment detection
    environment: Literal["auto", "jupyter", "colab", "standalone"] = Field(
        default="auto", description="Execution environment"
    )
    
    # Performance settings
    max_data_rows: int = Field(
        default=1_000_000, description="Maximum rows for data processing"
    )
    geocoding_rate_limit: float = Field(
        default=1.0, description="Geocoding API rate limit (requests per second)"
    )
    cache_enabled: bool = Field(
        default=True, description="Enable caching for expensive operations"
    )
    cache_ttl_seconds: int = Field(
        default=3600, description="Cache time-to-live in seconds"
    )
    
    # Visualization settings
    default_plot_height: int = Field(
        default=500, description="Default plot height in pixels"
    )
    default_plot_width: int = Field(
        default=700, description="Default plot width in pixels"
    )
    plot_dpi: int = Field(default=120, description="Default plot DPI")
    
    # Export settings
    export_formats: List[str] = Field(
        default=["csv", "excel", "json", "parquet"],
        description="Supported export formats"
    )
    
    # Data processing settings
    chunk_size: int = Field(
        default=10_000, description="Chunk size for large data processing"
    )
    memory_threshold_mb: int = Field(
        default=500, description="Memory threshold for chunked processing (MB)"
    )
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(
        default=None, description="Log file path (None for console only)"
    )
    
    # UI settings
    widget_layout_width: str = Field(
        default="100%", description="Default widget layout width"
    )
    show_progress_bars: bool = Field(
        default=True, description="Show progress bars for long operations"
    )
    
    @field_validator("environment")
    @classmethod
    def resolve_auto_environment(cls, v):
        """Resolve 'auto' environment to actual environment."""
        if v == "auto":
            return detect_environment()
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("export_formats")
    @classmethod
    def validate_export_formats(cls, v):
        """Validate export formats."""
        valid_formats = ["csv", "excel", "json", "parquet", "pickle"]
        for fmt in v:
            if fmt not in valid_formats:
                raise ValueError(f"Export format '{fmt}' not supported")
        return v
    
    class Config:
        env_file = ".env"
        env_prefix = "DATAVIZTEST_"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance.
    
    Returns:
        Settings instance
    """
    return settings


def update_settings(**kwargs) -> None:
    """Update global settings.
    
    Args:
        **kwargs: Settings to update
    """
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)


def is_jupyter_environment() -> bool:
    """Check if running in Jupyter environment.
    
    Returns:
        True if in Jupyter/Colab environment
    """
    return settings.environment in ["jupyter", "colab"]


def is_colab_environment() -> bool:
    """Check if running in Google Colab.
    
    Returns:
        True if in Google Colab
    """
    return settings.environment == "colab"