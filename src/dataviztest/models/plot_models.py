"""Plot and visualization models for DataVizTest application.

This module defines models for plot configurations, styling, and visualization options.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class PlotType(str, Enum):
    """Supported plot types."""
    SCATTER = "scatter"
    LINE = "line"
    BAR = "bar"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    HEATMAP = "heatmap"
    PIE = "pie"
    AREA = "area"
    BUBBLE = "bubble"
    TREEMAP = "treemap"
    SUNBURST = "sunburst"
    PARALLEL_COORDINATES = "parallel_coordinates"
    PARALLEL_CATEGORIES = "parallel_categories"


class AggregationMethod(str, Enum):
    """Data aggregation methods."""
    NONE = "none"
    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    STD = "std"
    VAR = "var"


class ColorScale(str, Enum):
    """Color scales for visualizations."""
    VIRIDIS = "viridis"
    PLASMA = "plasma"
    INFERNO = "inferno"
    MAGMA = "magma"
    BLUES = "blues"
    REDS = "reds"
    GREENS = "greens"
    RAINBOW = "rainbow"
    TURBO = "turbo"
    PLOTLY = "plotly"


class PlotTheme(str, Enum):
    """Plot themes."""
    DEFAULT = "default"
    PLOTLY = "plotly"
    PLOTLY_WHITE = "plotly_white"
    PLOTLY_DARK = "plotly_dark"
    GGPLOT2 = "ggplot2"
    SEABORN = "seaborn"
    SIMPLE_WHITE = "simple_white"
    PRESENTATION = "presentation"


class PlotStyling(BaseModel):
    """Plot styling configuration."""
    
    theme: PlotTheme = Field(default=PlotTheme.DEFAULT, description="Plot theme")
    color_scale: ColorScale = Field(default=ColorScale.VIRIDIS, description="Color scale")
    colors: Optional[List[str]] = Field(None, description="Custom color palette")
    width: int = Field(default=700, description="Plot width in pixels")
    height: int = Field(default=500, description="Plot height in pixels")
    font_family: str = Field(default="Arial", description="Font family")
    font_size: int = Field(default=12, description="Base font size")
    title_font_size: int = Field(default=16, description="Title font size")
    show_grid: bool = Field(default=True, description="Whether to show grid lines")
    grid_color: str = Field(default="lightgray", description="Grid line color")
    background_color: str = Field(default="white", description="Plot background color")
    margin: Dict[str, int] = Field(
        default_factory=lambda: {"l": 60, "r": 60, "t": 60, "b": 60},
        description="Plot margins"
    )


class AxisConfig(BaseModel):
    """Axis configuration."""
    
    title: str = Field(..., description="Axis title")
    show_title: bool = Field(default=True, description="Whether to show axis title")
    title_font_size: int = Field(default=14, description="Axis title font size")
    tick_font_size: int = Field(default=12, description="Tick label font size")
    show_ticks: bool = Field(default=True, description="Whether to show tick marks")
    tick_angle: int = Field(default=0, description="Tick label rotation angle")
    log_scale: bool = Field(default=False, description="Whether to use log scale")
    reverse: bool = Field(default=False, description="Whether to reverse axis direction")
    range: Optional[List[Union[float, str]]] = Field(None, description="Axis range")


class ColorConfig(BaseModel):
    """Color configuration."""
    
    palette: str = Field(default="viridis", description="Color palette name")
    colors: Optional[List[str]] = Field(None, description="Custom color list")
    reverse: bool = Field(default=False, description="Whether to reverse color scale")
    opacity: float = Field(default=1.0, description="Color opacity")


class StyleConfig(BaseModel):
    """Style configuration."""
    
    color_scheme: str = Field(default="viridis", description="Color scheme")
    width: int = Field(default=800, description="Plot width")
    height: int = Field(default=600, description="Plot height")
    theme: str = Field(default="plotly", description="Plot theme")
    font_family: str = Field(default="Arial", description="Font family")
    font_size: int = Field(default=12, description="Font size")
    background_color: str = Field(default="white", description="Background color")


class LegendConfig(BaseModel):
    """Legend configuration."""
    
    show: bool = Field(default=True, description="Whether to show legend")
    position: str = Field(default="right", description="Legend position")
    orientation: str = Field(default="vertical", description="Legend orientation")
    font_size: int = Field(default=12, description="Legend font size")
    background_color: str = Field(default="white", description="Legend background color")
    border_color: str = Field(default="black", description="Legend border color")
    border_width: int = Field(default=1, description="Legend border width")
    
    # Position validation moved to application logic
    
    # Orientation validation moved to application logic


class PlotConfig(BaseModel):
    """Complete plot configuration."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique plot ID")
    title: str = Field(..., description="Plot title")
    plot_type: PlotType = Field(..., description="Type of plot")
    
    # Data mapping
    x_column: Optional[str] = Field(None, description="X-axis column")
    y_column: Optional[str] = Field(None, description="Y-axis column")
    color_column: Optional[str] = Field(None, description="Color mapping column")
    size_column: Optional[str] = Field(None, description="Size mapping column")
    facet_column: Optional[str] = Field(None, description="Faceting column")
    
    # Grouping and aggregation
    grouping_columns: List[str] = Field(default_factory=list, description="Columns to group by")
    aggregation_method: AggregationMethod = Field(
        default=AggregationMethod.NONE, 
        description="Data aggregation method"
    )
    
    # Styling
    styling: PlotStyling = Field(default_factory=PlotStyling, description="Plot styling")
    x_axis: Optional[AxisConfig] = Field(None, description="X-axis configuration")
    y_axis: Optional[AxisConfig] = Field(None, description="Y-axis configuration")
    legend: LegendConfig = Field(default_factory=LegendConfig, description="Legend configuration")
    
    # Advanced options
    show_hover: bool = Field(default=True, description="Whether to show hover information")
    hover_columns: List[str] = Field(default_factory=list, description="Additional hover columns")
    annotations: List[Dict[str, Any]] = Field(default_factory=list, description="Plot annotations")
    
    # Interactivity
    enable_zoom: bool = Field(default=True, description="Enable zoom functionality")
    enable_pan: bool = Field(default=True, description="Enable pan functionality")
    enable_selection: bool = Field(default=False, description="Enable data selection")
    
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    # Additional configuration
    columns: Dict[str, Any] = Field(default_factory=dict, description="Column mappings")
    
    # Plot validation moved to application logic


class MapType(str, Enum):
    """Map visualization types."""
    SCATTER_MAP = "scatter_map"
    CHOROPLETH = "choropleth"
    HEATMAP = "heatmap"
    BUBBLE_MAP = "bubble_map"
    LINE_MAP = "line_map"


class MapConfig(BaseModel):
    """Map visualization configuration."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique map ID")
    map_type: MapType = Field(..., description="Type of map visualization")
    
    # Data mapping  
    columns: Dict[str, Any] = Field(default_factory=dict, description="Column mappings")
    
    # Location configuration
    location: Dict[str, Any] = Field(default_factory=dict, description="Location settings")
    
    # Style configuration
    style: Optional[StyleConfig] = Field(None, description="Style configuration")
    
    # Additional settings
    title: Optional[str] = Field(None, description="Map title")
    
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    show_legend: bool = Field(default=True, description="Show map legend")
    
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")


class VisualizationExport(BaseModel):
    """Export configuration for visualizations."""
    
    format: str = Field(..., description="Export format")
    filename: str = Field(..., description="Export filename")
    width: Optional[int] = Field(None, description="Export width")
    height: Optional[int] = Field(None, description="Export height")
    dpi: int = Field(default=300, description="Export DPI")
    include_data: bool = Field(default=False, description="Include underlying data")
    
    # Format validation moved to application logic


class PlotResult(BaseModel):
    """Result of plot generation."""
    
    plot_id: str = Field(..., description="Plot ID")
    success: bool = Field(..., description="Whether plot generation succeeded")
    plot_object: Optional[Any] = Field(None, description="Generated plot object")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    generation_time_ms: float = Field(..., description="Plot generation time in milliseconds")
    data_points: int = Field(..., description="Number of data points plotted")
    warnings: List[str] = Field(default_factory=list, description="Generation warnings")
    
    class Config:
        arbitrary_types_allowed = True  # Allow plot objects