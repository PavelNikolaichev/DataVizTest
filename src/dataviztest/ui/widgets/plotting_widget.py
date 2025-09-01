"""Plotting widget for interactive visualization creation.

This module provides a comprehensive plotting interface that allows
users to create and customize various types of plots.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

import ipywidgets as widgets
import pandas as pd

from .base_widget import InteractiveWidget
from ..interactive_components import (
    DataColumnSelector,
    ValueRangeSelector,
    CategorySelector,
    ActionButton,
    MessageDisplay
)
from ...infrastructure import get_logger, handle_errors
from ...models import (
    PlotConfig,
    PlotType,
    StyleConfig,
    LegendConfig,
    AxisConfig,
    ColorConfig,
)
from ...services import ApplicationService


class PlottingWidget(InteractiveWidget):
    """Widget for creating and configuring data visualizations."""
    
    def __init__(
        self,
        app_service: Optional[ApplicationService] = None,
        **kwargs
    ):
        """Initialize the plotting widget.
        
        Args:
            app_service: Application service for data operations
            **kwargs: Additional widget arguments
        """
        super().__init__(app_service=app_service, **kwargs)
        
        # Plot state
        self._current_plot_config: Optional[PlotConfig] = None
        self._last_plot_result: Optional[Any] = None
        
        # UI components
        self._plot_type_selector: Optional[widgets.Dropdown] = None
        self._column_selectors: Dict[str, DataColumnSelector] = {}
        self._style_controls: Optional[widgets.Widget] = None
        self._plot_display: Optional[widgets.Output] = None
        self._message_display: Optional[MessageDisplay] = None
        
        self.logger = get_logger(__name__)
    
    def _create_widget(self) -> widgets.Widget:
        """Create the plotting widget interface."""
        # Title
        title = widgets.HTML("<h3>Data Visualization</h3>")
        
        # Message display
        self._message_display = MessageDisplay()
        
        # Plot type selector
        self._plot_type_selector = widgets.Dropdown(
            options=[
                ('Scatter Plot', PlotType.SCATTER),
                ('Line Plot', PlotType.LINE),
                ('Bar Chart', PlotType.BAR),
                ('Histogram', PlotType.HISTOGRAM),
                ('Box Plot', PlotType.BOX),
                ('Heatmap', PlotType.HEATMAP),
                ('Distribution Plot', PlotType.DISTRIBUTION)
            ],
            description='Plot Type:',
            layout=widgets.Layout(width='300px')
        )
        self._plot_type_selector.observe(self._on_plot_type_change, names='value')
        
        # Column selection container
        self._column_selection_container = widgets.VBox()
        
        # Style controls container
        self._style_controls_container = widgets.VBox()
        
        # Action buttons
        self._create_plot_button = ActionButton(
            "Create Plot",
            button_style='primary',
            icon='bar-chart'
        )
        self._create_plot_button.add_click_callback(self._create_plot)
        
        self._export_plot_button = ActionButton(
            "Export Plot",
            button_style='info',
            icon='download'
        )
        self._export_plot_button.add_click_callback(self._export_plot)
        
        # Plot display area
        self._plot_display = widgets.Output()
        
        # Layout
        plot_configuration = widgets.VBox([
            widgets.HTML("<h4>Plot Configuration</h4>"),
            self._plot_type_selector,
            self._column_selection_container,
            self._style_controls_container,
            widgets.HBox([
                self._create_plot_button.widget,
                self._export_plot_button.widget
            ])
        ])
        
        plot_output = widgets.VBox([
            widgets.HTML("<h4>Plot Output</h4>"),
            self._plot_display
        ])
        
        return widgets.VBox([
            title,
            self._message_display.widget,
            plot_configuration,
            plot_output
        ])
    
    def _setup_interactions(self) -> None:
        """Set up widget interactions."""
        # Update interface when data changes
        if self.app_service:
            self.add_callback("state_change", self._on_data_change)
        
        # Initialize with default plot type
        self._update_column_selectors()
        self._update_style_controls()
    
    def _on_data_change(self, state) -> None:
        """Handle data changes."""
        current_data = self.app_service.current_data
        if current_data is not None:
            self._update_column_selectors()
            self._message_display.show_message(
                f"Data updated: {current_data.shape[0]} rows, {current_data.shape[1]} columns",
                "info"
            )
    
    def _on_plot_type_change(self, change: Dict[str, Any]) -> None:
        """Handle plot type change."""
        self._update_column_selectors()
        self._update_style_controls()
    
    def _update_column_selectors(self) -> None:
        """Update column selectors based on plot type and available data."""
        if not self.app_service or self.app_service.current_data is None:
            return
        
        data = self.app_service.current_data
        plot_type = self._plot_type_selector.value if self._plot_type_selector else PlotType.SCATTER
        
        # Clear existing selectors
        self._column_selectors.clear()
        
        # Create selectors based on plot type
        selectors = []
        
        if plot_type == PlotType.SCATTER:
            self._column_selectors['x'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="X-axis:",
                multi_select=False
            )
            self._column_selectors['y'] = DataColumnSelector(
                data=data,
                column_types=['numeric'], 
                description="Y-axis:",
                multi_select=False
            )
            self._column_selectors['color'] = DataColumnSelector(
                data=data,
                column_types=['categorical', 'numeric'],
                description="Color by:",
                multi_select=False,
                allow_none=True
            )
            selectors.extend([
                self._column_selectors['x'].widget,
                self._column_selectors['y'].widget,
                self._column_selectors['color'].widget
            ])
            
        elif plot_type == PlotType.LINE:
            self._column_selectors['x'] = DataColumnSelector(
                data=data,
                column_types=['numeric', 'datetime'],
                description="X-axis:",
                multi_select=False
            )
            self._column_selectors['y'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="Y-axis:",
                multi_select=False
            )
            selectors.extend([
                self._column_selectors['x'].widget,
                self._column_selectors['y'].widget
            ])
            
        elif plot_type == PlotType.BAR:
            self._column_selectors['x'] = DataColumnSelector(
                data=data,
                column_types=['categorical'],
                description="Categories:",
                multi_select=False
            )
            self._column_selectors['y'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="Values:",
                multi_select=False
            )
            selectors.extend([
                self._column_selectors['x'].widget,
                self._column_selectors['y'].widget
            ])
            
        elif plot_type == PlotType.HISTOGRAM:
            self._column_selectors['x'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="Column:",
                multi_select=False
            )
            selectors.append(self._column_selectors['x'].widget)
            
        elif plot_type == PlotType.BOX:
            self._column_selectors['y'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="Values:",
                multi_select=False
            )
            self._column_selectors['x'] = DataColumnSelector(
                data=data,
                column_types=['categorical'],
                description="Groups:",
                multi_select=False,
                allow_none=True
            )
            selectors.extend([
                self._column_selectors['y'].widget,
                self._column_selectors['x'].widget
            ])
            
        elif plot_type == PlotType.HEATMAP:
            self._column_selectors['columns'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="Columns:",
                multi_select=True
            )
            selectors.append(self._column_selectors['columns'].widget)
            
        elif plot_type == PlotType.DISTRIBUTION:
            self._column_selectors['x'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="Column:",
                multi_select=False
            )
            selectors.append(self._column_selectors['x'].widget)
        
        # Update container
        self._column_selection_container.children = selectors
        
        # Add change callbacks
        for selector in self._column_selectors.values():
            selector.add_change_callback(self._on_column_selection_change)
    
    def _on_column_selection_change(self, column_name: str) -> None:
        """Handle column selection change."""
        # Could trigger preview or validation here
        pass
    
    def _update_style_controls(self) -> None:
        """Update style controls based on plot type."""
        plot_type = self._plot_type_selector.value if self._plot_type_selector else PlotType.SCATTER
        
        # Common style controls
        controls = []
        
        # Title input
        self._title_input = widgets.Text(
            description="Title:",
            placeholder="Enter plot title",
            layout=widgets.Layout(width='400px')
        )
        controls.append(self._title_input)
        
        # Color scheme selector
        self._color_scheme = widgets.Dropdown(
            options=[
                ('Default', 'plotly'),
                ('Viridis', 'viridis'),
                ('Plasma', 'plasma'),
                ('Blues', 'blues'),
                ('Greens', 'greens'),
                ('Reds', 'reds')
            ],
            description="Color scheme:",
            value='plotly'
        )
        controls.append(self._color_scheme)
        
        # Size controls for scatter plots
        if plot_type == PlotType.SCATTER:
            self._marker_size = widgets.IntSlider(
                value=8,
                min=3,
                max=20,
                description="Marker size:",
                continuous_update=False
            )
            controls.append(self._marker_size)
        
        # Orientation for bar plots
        if plot_type == PlotType.BAR:
            self._orientation = widgets.Dropdown(
                options=[('Vertical', 'v'), ('Horizontal', 'h')],
                description="Orientation:",
                value='v'
            )
            controls.append(self._orientation)
        
        # Bins for histogram
        if plot_type == PlotType.HISTOGRAM:
            self._bins = widgets.IntSlider(
                value=30,
                min=5,
                max=100,
                description="Number of bins:",
                continuous_update=False
            )
            controls.append(self._bins)
        
        # Legend controls
        self._show_legend = widgets.Checkbox(
            value=True,
            description="Show legend"
        )
        controls.append(self._show_legend)
        
        # Width and height
        self._plot_width = widgets.IntSlider(
            value=800,
            min=400,
            max=1200,
            description="Width:",
            continuous_update=False
        )
        controls.append(self._plot_width)
        
        self._plot_height = widgets.IntSlider(
            value=600,
            min=300,
            max=900,
            description="Height:",
            continuous_update=False
        )
        controls.append(self._plot_height)
        
        # Update container
        self._style_controls_container.children = [
            widgets.HTML("<h5>Style Options</h5>")
        ] + controls
    
    @handle_errors("plot creation")
    def _create_plot(self) -> None:
        """Create a plot based on current configuration."""
        if not self.app_service or self.app_service.current_data is None:
            self._message_display.show_message("No data available for plotting", "error")
            return
        
        # Validate column selections
        if not self._validate_column_selections():
            return
        
        # Build plot configuration
        plot_config = self._build_plot_config()
        if not plot_config:
            return
        
        try:
            # Create the plot
            self._message_display.show_message("Creating plot...", "info")
            result = self.app_service.create_visualization(plot_config)
            
            # Display the plot
            with self._plot_display:
                self._plot_display.clear_output()
                if hasattr(result, 'show'):
                    result.show()
                else:
                    print(result)
            
            self._last_plot_result = result
            self._current_plot_config = plot_config
            
            self._message_display.show_message("Plot created successfully!", "success")
            
        except Exception as e:
            self.logger.error(f"Failed to create plot: {e}")
            self._message_display.show_message(f"Failed to create plot: {str(e)}", "error")
    
    def _validate_column_selections(self) -> bool:
        """Validate that required columns are selected."""
        plot_type = self._plot_type_selector.value
        
        required_columns = {
            PlotType.SCATTER: ['x', 'y'],
            PlotType.LINE: ['x', 'y'],
            PlotType.BAR: ['x', 'y'],
            PlotType.HISTOGRAM: ['x'],
            PlotType.BOX: ['y'],
            PlotType.HEATMAP: ['columns'],
            PlotType.DISTRIBUTION: ['x']
        }
        
        required = required_columns.get(plot_type, [])
        
        for col_key in required:
            selector = self._column_selectors.get(col_key)
            if not selector or not selector.value:
                self._message_display.show_message(
                    f"Please select a column for {col_key}",
                    "warning"
                )
                return False
        
        return True
    
    def _build_plot_config(self) -> Optional[PlotConfig]:
        """Build plot configuration from current widget state."""
        try:
            plot_type = self._plot_type_selector.value
            
            # Build column mappings
            columns = {}
            for key, selector in self._column_selectors.items():
                if selector.value:
                    columns[key] = selector.value
            
            # Build style configuration
            style_config = StyleConfig(
                color_scheme=self._color_scheme.value,
                width=self._plot_width.value,
                height=self._plot_height.value,
            )
            
            # Build legend configuration
            legend_config = LegendConfig(
                show=self._show_legend.value,
                position='right',
                orientation='vertical'
            )
            
            # Plot-specific configuration
            plot_kwargs = {}
            
            if plot_type == PlotType.SCATTER and hasattr(self, '_marker_size'):
                plot_kwargs['marker_size'] = self._marker_size.value
            
            if plot_type == PlotType.BAR and hasattr(self, '_orientation'):
                plot_kwargs['orientation'] = self._orientation.value
            
            if plot_type == PlotType.HISTOGRAM and hasattr(self, '_bins'):
                plot_kwargs['bins'] = self._bins.value
            
            # Create plot configuration
            plot_config = PlotConfig(
                plot_type=plot_type,
                columns=columns,
                title=self._title_input.value or f"{plot_type.value.title()} Plot",
                style=style_config,
                legend=legend_config,
                **plot_kwargs
            )
            
            return plot_config
            
        except Exception as e:
            self.logger.error(f"Failed to build plot config: {e}")
            self._message_display.show_message(
                f"Configuration error: {str(e)}",
                "error"
            )
            return None
    
    def _export_plot(self) -> None:
        """Export the current plot."""
        if not self._last_plot_result:
            self._message_display.show_message("No plot to export", "warning")
            return
        
        # In a real implementation, this would open a file dialog
        # For now, we'll just show a message
        self._message_display.show_message(
            "Export functionality would be implemented here",
            "info"
        )
    
    @property
    def current_plot_config(self) -> Optional[PlotConfig]:
        """Get the current plot configuration."""
        return self._current_plot_config
    
    @property
    def last_plot_result(self) -> Optional[Any]:
        """Get the last plot result."""
        return self._last_plot_result
    
    def set_plot_type(self, plot_type: PlotType) -> None:
        """Set the plot type programmatically."""
        if self._plot_type_selector:
            self._plot_type_selector.value = plot_type
    
    def get_available_columns(self) -> Dict[str, List[str]]:
        """Get available columns by type."""
        if not self.app_service or self.app_service.current_data is None:
            return {}
        
        data = self.app_service.current_data
        return {
            'numeric': data.select_dtypes(include=['number']).columns.tolist(),
            'categorical': data.select_dtypes(include=['object', 'category']).columns.tolist(),
            'datetime': data.select_dtypes(include=['datetime']).columns.tolist()
        }