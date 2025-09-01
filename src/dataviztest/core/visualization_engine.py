"""Visualization engine for DataVizTest application.

This module provides visualization capabilities using multiple rendering backends
(Plotly, Matplotlib) with a unified interface.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.figure
import numpy as np

from ..infrastructure import (
    VisualizationError,
    PlotConfigurationError,
    RenderingError,
    get_logger,
    log_performance,
    handle_errors,
)
from ..models import (
    PlotConfig,
    PlotResult,
    PlotType,
    AggregationMethod,
    MapConfig,
    MapType,
)


class BaseRenderer(ABC):
    """Abstract base class for plot renderers."""
    
    def __init__(self):
        """Initialize the renderer."""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def render(self, data: pd.DataFrame, config: PlotConfig) -> Any:
        """Render a plot with the given data and configuration.
        
        Args:
            data: DataFrame to plot
            config: Plot configuration
            
        Returns:
            Plot object
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: PlotConfig) -> bool:
        """Validate if the configuration is supported by this renderer.
        
        Args:
            config: Plot configuration
            
        Returns:
            True if configuration is valid
        """
        pass
    
    def _aggregate_data(self, data: pd.DataFrame, config: PlotConfig) -> pd.DataFrame:
        """Aggregate data based on configuration.
        
        Args:
            data: Input data
            config: Plot configuration
            
        Returns:
            Aggregated data
        """
        if (config.aggregation_method == AggregationMethod.NONE or 
            not config.grouping_columns):
            return data
        
        # Group by specified columns
        grouped = data.groupby(config.grouping_columns)
        
        # Apply aggregation
        if config.aggregation_method == AggregationMethod.SUM:
            return grouped.sum().reset_index()
        elif config.aggregation_method == AggregationMethod.MEAN:
            return grouped.mean().reset_index()
        elif config.aggregation_method == AggregationMethod.MEDIAN:
            return grouped.median().reset_index()
        elif config.aggregation_method == AggregationMethod.COUNT:
            return grouped.count().reset_index()
        elif config.aggregation_method == AggregationMethod.MIN:
            return grouped.min().reset_index()
        elif config.aggregation_method == AggregationMethod.MAX:
            return grouped.max().reset_index()
        elif config.aggregation_method == AggregationMethod.STD:
            return grouped.std().reset_index()
        elif config.aggregation_method == AggregationMethod.VAR:
            return grouped.var().reset_index()
        else:
            return data


class PlotlyRenderer(BaseRenderer):
    """Plotly-based renderer for interactive plots."""
    
    def validate_config(self, config: PlotConfig) -> bool:
        """Validate plot configuration for Plotly renderer."""
        required_columns = self._get_required_columns(config.plot_type)
        
        for col_type, col_name in required_columns.items():
            if col_name and not getattr(config, col_name):
                return False
        
        return True
    
    def _get_required_columns(self, plot_type: PlotType) -> Dict[str, str]:
        """Get required columns for each plot type."""
        requirements = {
            PlotType.SCATTER: {"x": "x_column", "y": "y_column"},
            PlotType.LINE: {"x": "x_column", "y": "y_column"},
            PlotType.BAR: {"x": "x_column", "y": "y_column"},
            PlotType.HISTOGRAM: {"x": "x_column"},
            PlotType.BOX: {"y": "y_column"},
            PlotType.PIE: {"color": "color_column"},
            PlotType.HEATMAP: {"x": "x_column", "y": "y_column"},
            PlotType.BUBBLE: {"x": "x_column", "y": "y_column", "size": "size_column"},
        }
        return requirements.get(plot_type, {})
    
    @handle_errors("plot rendering")
    def render(self, data: pd.DataFrame, config: PlotConfig) -> go.Figure:
        """Render plot using Plotly."""
        # Aggregate data if needed
        plot_data = self._aggregate_data(data, config)
        
        # Create plot based on type
        if config.plot_type == PlotType.SCATTER:
            fig = self._create_scatter(plot_data, config)
        elif config.plot_type == PlotType.LINE:
            fig = self._create_line(plot_data, config)
        elif config.plot_type == PlotType.BAR:
            fig = self._create_bar(plot_data, config)
        elif config.plot_type == PlotType.HISTOGRAM:
            fig = self._create_histogram(plot_data, config)
        elif config.plot_type == PlotType.BOX:
            fig = self._create_box(plot_data, config)
        elif config.plot_type == PlotType.PIE:
            fig = self._create_pie(plot_data, config)
        elif config.plot_type == PlotType.HEATMAP:
            fig = self._create_heatmap(plot_data, config)
        elif config.plot_type == PlotType.BUBBLE:
            fig = self._create_bubble(plot_data, config)
        else:
            raise PlotConfigurationError(f"Unsupported plot type: {config.plot_type}")
        
        # Apply styling
        self._apply_styling(fig, config)
        
        return fig
    
    def _create_scatter(self, data: pd.DataFrame, config: PlotConfig) -> go.Figure:
        """Create scatter plot."""
        kwargs = {
            "x": config.x_column,
            "y": config.y_column,
            "title": config.title,
        }
        
        if config.color_column:
            kwargs["color"] = config.color_column
        if config.size_column:
            kwargs["size"] = config.size_column
        if config.facet_column:
            kwargs["facet_col"] = config.facet_column
        if config.hover_columns:
            kwargs["hover_data"] = config.hover_columns
        
        return px.scatter(data, **kwargs)
    
    def _create_line(self, data: pd.DataFrame, config: PlotConfig) -> go.Figure:
        """Create line plot."""
        kwargs = {
            "x": config.x_column,
            "y": config.y_column,
            "title": config.title,
        }
        
        if config.color_column:
            kwargs["color"] = config.color_column
        if config.facet_column:
            kwargs["facet_col"] = config.facet_column
        if config.hover_columns:
            kwargs["hover_data"] = config.hover_columns
        
        return px.line(data, **kwargs)
    
    def _create_bar(self, data: pd.DataFrame, config: PlotConfig) -> go.Figure:
        """Create bar plot."""
        kwargs = {
            "x": config.x_column,
            "y": config.y_column,
            "title": config.title,
        }
        
        if config.color_column:
            kwargs["color"] = config.color_column
        if config.facet_column:
            kwargs["facet_col"] = config.facet_column
        if config.hover_columns:
            kwargs["hover_data"] = config.hover_columns
        
        return px.bar(data, **kwargs)
    
    def _create_histogram(self, data: pd.DataFrame, config: PlotConfig) -> go.Figure:
        """Create histogram."""
        kwargs = {
            "x": config.x_column,
            "title": config.title,
        }
        
        if config.color_column:
            kwargs["color"] = config.color_column
        if config.facet_column:
            kwargs["facet_col"] = config.facet_column
        
        return px.histogram(data, **kwargs)
    
    def _create_box(self, data: pd.DataFrame, config: PlotConfig) -> go.Figure:
        """Create box plot."""
        kwargs = {
            "y": config.y_column,
            "title": config.title,
        }
        
        if config.x_column:
            kwargs["x"] = config.x_column
        if config.color_column:
            kwargs["color"] = config.color_column
        if config.facet_column:
            kwargs["facet_col"] = config.facet_column
        
        return px.box(data, **kwargs)
    
    def _create_pie(self, data: pd.DataFrame, config: PlotConfig) -> go.Figure:
        """Create pie chart."""
        # For pie charts, we need to aggregate by the color column
        if config.y_column:
            # Sum values by category
            pie_data = data.groupby(config.color_column)[config.y_column].sum().reset_index()
            values = config.y_column
        else:
            # Count occurrences
            pie_data = data[config.color_column].value_counts().reset_index()
            pie_data.columns = [config.color_column, 'count']
            values = 'count'
        
        return px.pie(
            pie_data,
            names=config.color_column,
            values=values,
            title=config.title
        )
    
    def _create_heatmap(self, data: pd.DataFrame, config: PlotConfig) -> go.Figure:
        """Create heatmap."""
        # Create pivot table for heatmap
        if config.y_column and config.color_column:
            pivot_data = data.pivot_table(
                index=config.y_column,
                columns=config.x_column,
                values=config.color_column,
                aggfunc='mean'
            )
        else:
            # Use correlation matrix if no specific values column
            numeric_data = data.select_dtypes(include=[np.number])
            pivot_data = numeric_data.corr()
        
        return px.imshow(
            pivot_data,
            title=config.title,
            aspect="auto"
        )
    
    def _create_bubble(self, data: pd.DataFrame, config: PlotConfig) -> go.Figure:
        """Create bubble chart."""
        kwargs = {
            "x": config.x_column,
            "y": config.y_column,
            "size": config.size_column,
            "title": config.title,
        }
        
        if config.color_column:
            kwargs["color"] = config.color_column
        if config.hover_columns:
            kwargs["hover_data"] = config.hover_columns
        
        return px.scatter(data, **kwargs)
    
    def _apply_styling(self, fig: go.Figure, config: PlotConfig) -> None:
        """Apply styling to the figure."""
        # Update layout
        layout_updates = {
            "width": config.styling.width,
            "height": config.styling.height,
            "font": {"family": config.styling.font_family, "size": config.styling.font_size},
            "title": {"font": {"size": config.styling.title_font_size}},
            "plot_bgcolor": config.styling.background_color,
            "margin": config.styling.margin,
        }
        
        if config.styling.theme != "default":
            layout_updates["template"] = config.styling.theme.value
        
        fig.update_layout(**layout_updates)
        
        # Update axes if configured
        if config.x_axis:
            fig.update_xaxes(
                title_text=config.x_axis.title if config.x_axis.show_title else "",
                title_font_size=config.x_axis.title_font_size,
                tickfont_size=config.x_axis.tick_font_size,
                showticklabels=config.x_axis.show_ticks,
                tickangle=config.x_axis.tick_angle,
                type="log" if config.x_axis.log_scale else "linear",
                autorange="reversed" if config.x_axis.reverse else True,
                range=config.x_axis.range,
                showgrid=config.styling.show_grid,
                gridcolor=config.styling.grid_color,
            )
        
        if config.y_axis:
            fig.update_yaxes(
                title_text=config.y_axis.title if config.y_axis.show_title else "",
                title_font_size=config.y_axis.title_font_size,
                tickfont_size=config.y_axis.tick_font_size,
                showticklabels=config.y_axis.show_ticks,
                tickangle=config.y_axis.tick_angle,
                type="log" if config.y_axis.log_scale else "linear",
                autorange="reversed" if config.y_axis.reverse else True,
                range=config.y_axis.range,
                showgrid=config.styling.show_grid,
                gridcolor=config.styling.grid_color,
            )
        
        # Update legend
        if not config.legend.show:
            fig.update_layout(showlegend=False)
        else:
            # Map orientation to Plotly values
            plotly_orientation = "v" if config.legend.orientation == "vertical" else "h"
            
            legend_updates = {
                "orientation": plotly_orientation,
                "font": {"size": config.legend.font_size},
                "bgcolor": config.legend.background_color,
                "bordercolor": config.legend.border_color,
                "borderwidth": config.legend.border_width,
            }
            
            # Position legend
            if config.legend.position == "top":
                legend_updates.update({"x": 0.5, "y": 1.1, "xanchor": "center"})
            elif config.legend.position == "bottom":
                legend_updates.update({"x": 0.5, "y": -0.1, "xanchor": "center"})
            elif config.legend.position == "left":
                legend_updates.update({"x": -0.1, "y": 0.5, "yanchor": "middle"})
            elif config.legend.position == "right":
                legend_updates.update({"x": 1.1, "y": 0.5, "yanchor": "middle"})
            
            fig.update_layout(legend=legend_updates)


class VisualizationEngine:
    """Main visualization engine that manages multiple renderers."""
    
    def __init__(self):
        """Initialize the visualization engine."""
        self.logger = get_logger(__name__)
        self._renderers: Dict[str, BaseRenderer] = {}
        self._default_renderer = "plotly"
        
        # Register default renderers
        self.register_renderer("plotly", PlotlyRenderer())
    
    def register_renderer(self, name: str, renderer: BaseRenderer) -> None:
        """Register a renderer.
        
        Args:
            name: Renderer name
            renderer: Renderer instance
        """
        self._renderers[name] = renderer
        self.logger.debug(f"Registered renderer: {name}")
    
    def get_available_renderers(self) -> List[str]:
        """Get list of available renderers.
        
        Returns:
            List of renderer names
        """
        return list(self._renderers.keys())
    
    def set_default_renderer(self, renderer_name: str) -> None:
        """Set the default renderer.
        
        Args:
            renderer_name: Name of renderer to use as default
        """
        if renderer_name not in self._renderers:
            raise VisualizationError(f"Unknown renderer: {renderer_name}")
        
        self._default_renderer = renderer_name
        self.logger.debug(f"Set default renderer to: {renderer_name}")
    
    @log_performance
    @handle_errors("plot creation")
    def create_plot(
        self, 
        data: pd.DataFrame, 
        config: PlotConfig,
        renderer: Optional[str] = None
    ) -> PlotResult:
        """Create a plot using the specified renderer.
        
        Args:
            data: Data to plot
            config: Plot configuration
            renderer: Renderer to use (default if None)
            
        Returns:
            Plot result with timing and metadata
        """
        start_time = time.time()
        renderer_name = renderer or self._default_renderer
        
        if renderer_name not in self._renderers:
            raise VisualizationError(f"Unknown renderer: {renderer_name}")
        
        renderer_obj = self._renderers[renderer_name]
        
        # Validate configuration
        if not renderer_obj.validate_config(config):
            raise PlotConfigurationError(
                f"Invalid configuration for {renderer_name} renderer"
            )
        
        # Validate data
        if data.empty:
            raise VisualizationError("Cannot create plot with empty data")
        
        warnings = []
        
        # Check for missing required columns
        required_columns = []
        if config.x_column:
            required_columns.append(config.x_column)
        if config.y_column:
            required_columns.append(config.y_column)
        if config.color_column:
            required_columns.append(config.color_column)
        if config.size_column:
            required_columns.append(config.size_column)
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise PlotConfigurationError(
                f"Missing required columns: {missing_columns}"
            )
        
        # Check for large datasets
        if len(data) > 100000:
            warnings.append(
                f"Large dataset ({len(data)} rows) may cause performance issues"
            )
        
        try:
            # Create the plot
            plot_object = renderer_obj.render(data, config)
            execution_time = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"Created {config.plot_type} plot with {len(data)} data points "
                f"in {execution_time:.2f}ms"
            )
            
            return PlotResult(
                plot_id=config.id,
                success=True,
                plot_object=plot_object,
                generation_time_ms=execution_time,
                data_points=len(data),
                warnings=warnings
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Failed to create plot: {str(e)}"
            
            self.logger.error(error_msg)
            
            return PlotResult(
                plot_id=config.id,
                success=False,
                error_message=error_msg,
                generation_time_ms=execution_time,
                data_points=len(data),
                warnings=warnings
            )
    
    def get_supported_plot_types(self, renderer: Optional[str] = None) -> List[PlotType]:
        """Get supported plot types for a renderer.
        
        Args:
            renderer: Renderer name (default if None)
            
        Returns:
            List of supported plot types
        """
        # For now, return all plot types for Plotly renderer
        # This could be extended to query each renderer's capabilities
        return list(PlotType)
    
    def validate_plot_config(self, config: PlotConfig, renderer: Optional[str] = None) -> bool:
        """Validate a plot configuration.
        
        Args:
            config: Plot configuration to validate
            renderer: Renderer to validate against (default if None)
            
        Returns:
            True if configuration is valid
        """
        renderer_name = renderer or self._default_renderer
        
        if renderer_name not in self._renderers:
            return False
        
        return self._renderers[renderer_name].validate_config(config)