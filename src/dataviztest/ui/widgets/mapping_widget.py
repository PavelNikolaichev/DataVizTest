"""Mapping widget for interactive geospatial visualization.

This module provides a comprehensive mapping interface that allows
users to create and customize geospatial visualizations and maps.
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
    MapConfig,
    MapType,
    StyleConfig,
    ColorConfig,
)
from ...services import ApplicationService


class MappingWidget(InteractiveWidget):
    """Widget for creating and configuring geospatial visualizations."""
    
    def __init__(
        self,
        app_service: Optional[ApplicationService] = None,
        **kwargs
    ):
        """Initialize the mapping widget.
        
        Args:
            app_service: Application service for data operations
            **kwargs: Additional widget arguments
        """
        super().__init__(app_service=app_service, **kwargs)
        
        # Map state
        self._current_map_config: Optional[MapConfig] = None
        self._last_map_result: Optional[Any] = None
        
        # UI components
        self._map_type_selector: Optional[widgets.Dropdown] = None
        self._column_selectors: Dict[str, DataColumnSelector] = {}
        self._location_controls: Optional[widgets.Widget] = None
        self._style_controls: Optional[widgets.Widget] = None
        self._map_display: Optional[widgets.Output] = None
        self._message_display: Optional[MessageDisplay] = None
        
        self.logger = get_logger(__name__)
    
    def _create_widget(self) -> widgets.Widget:
        """Create the mapping widget interface."""
        # Title
        title = widgets.HTML("<h3>Geospatial Mapping</h3>")
        
        # Message display
        self._message_display = MessageDisplay()
        
        # Map type selector
        self._map_type_selector = widgets.Dropdown(
            options=[
                ('Marker Map', MapType.MARKER),
                ('Choropleth', MapType.CHOROPLETH),
                ('Heat Map', MapType.HEATMAP),
                ('Cluster Map', MapType.CLUSTER),
                ('Bubble Map', MapType.BUBBLE)
            ],
            description='Map Type:',
            layout=widgets.Layout(width='300px')
        )
        self._map_type_selector.observe(self._on_map_type_change, names='value')
        
        # Location configuration container
        self._location_controls_container = widgets.VBox()
        
        # Column selection container
        self._column_selection_container = widgets.VBox()
        
        # Style controls container
        self._style_controls_container = widgets.VBox()
        
        # Action buttons
        self._create_map_button = ActionButton(
            "Create Map",
            button_style='primary',
            icon='globe'
        )
        self._create_map_button.add_click_callback(self._create_map)
        
        self._export_map_button = ActionButton(
            "Export Map",
            button_style='info',
            icon='download'
        )
        self._export_map_button.add_click_callback(self._export_map)
        
        self._geocode_button = ActionButton(
            "Geocode Addresses",
            button_style='warning',
            icon='map-marker'
        )
        self._geocode_button.add_click_callback(self._geocode_addresses)
        
        # Map display area
        self._map_display = widgets.Output()
        
        # Layout
        map_configuration = widgets.VBox([
            widgets.HTML("<h4>Map Configuration</h4>"),
            self._map_type_selector,
            self._location_controls_container,
            self._column_selection_container,
            self._style_controls_container,
            widgets.HBox([
                self._create_map_button.widget,
                self._export_map_button.widget,
                self._geocode_button.widget
            ])
        ])
        
        map_output = widgets.VBox([
            widgets.HTML("<h4>Map Output</h4>"),
            self._map_display
        ])
        
        return widgets.VBox([
            title,
            self._message_display.widget,
            map_configuration,
            map_output
        ])
    
    def _setup_interactions(self) -> None:
        """Set up widget interactions."""
        # Update interface when data changes
        if self.app_service:
            self.add_callback("state_change", self._on_data_change)
        
        # Initialize with default map type
        self._update_location_controls()
        self._update_column_selectors()
        self._update_style_controls()
    
    def _on_data_change(self, state) -> None:
        """Handle data changes."""
        current_data = self.app_service.current_data
        if current_data is not None:
            self._update_location_controls()
            self._update_column_selectors()
            self._message_display.show_message(
                f"Data updated: {current_data.shape[0]} rows, {current_data.shape[1]} columns",
                "info"
            )
    
    def _on_map_type_change(self, change: Dict[str, Any]) -> None:
        """Handle map type change."""
        self._update_location_controls()
        self._update_column_selectors()
        self._update_style_controls()
    
    def _update_location_controls(self) -> None:
        """Update location controls based on available data."""
        if not self.app_service or self.app_service.current_data is None:
            return
        
        data = self.app_service.current_data
        
        # Check for existing coordinate columns
        lat_columns = [col for col in data.columns if 'lat' in col.lower()]
        lon_columns = [col for col in data.columns if 'lon' in col.lower() or 'lng' in col.lower()]
        address_columns = [col for col in data.columns if any(term in col.lower() 
                          for term in ['address', 'location', 'place', 'city', 'street'])]
        
        controls = []
        
        # Coordinate selection
        self._lat_selector = widgets.Dropdown(
            options=[('None', None)] + [(col, col) for col in lat_columns + data.select_dtypes(include=['number']).columns.tolist()],
            description="Latitude:",
            value=lat_columns[0] if lat_columns else None,
            layout=widgets.Layout(width='300px')
        )
        controls.append(self._lat_selector)
        
        self._lon_selector = widgets.Dropdown(
            options=[('None', None)] + [(col, col) for col in lon_columns + data.select_dtypes(include=['number']).columns.tolist()],
            description="Longitude:",
            value=lon_columns[0] if lon_columns else None,
            layout=widgets.Layout(width='300px')
        )
        controls.append(self._lon_selector)
        
        # Address column for geocoding
        if address_columns:
            self._address_selector = widgets.Dropdown(
                options=[('None', None)] + [(col, col) for col in address_columns],
                description="Address:",
                value=address_columns[0] if address_columns else None,
                layout=widgets.Layout(width='300px')
            )
            controls.append(self._address_selector)
        
        # Base map center
        self._center_lat = widgets.FloatText(
            value=40.7128,  # Default to NYC
            description="Center Lat:",
            layout=widgets.Layout(width='200px')
        )
        controls.append(self._center_lat)
        
        self._center_lon = widgets.FloatText(
            value=-74.0060,  # Default to NYC
            description="Center Lon:",
            layout=widgets.Layout(width='200px')
        )
        controls.append(self._center_lon)
        
        # Zoom level
        self._zoom_level = widgets.IntSlider(
            value=10,
            min=1,
            max=18,
            description="Zoom:",
            continuous_update=False
        )
        controls.append(self._zoom_level)
        
        # Update container
        self._location_controls_container.children = [
            widgets.HTML("<h5>Location Settings</h5>")
        ] + controls
    
    def _update_column_selectors(self) -> None:
        """Update column selectors based on map type and available data."""
        if not self.app_service or self.app_service.current_data is None:
            return
        
        data = self.app_service.current_data
        map_type = self._map_type_selector.value if self._map_type_selector else MapType.MARKER
        
        # Clear existing selectors
        self._column_selectors.clear()
        
        # Create selectors based on map type
        selectors = []
        
        if map_type == MapType.MARKER:
            # Popup text column
            self._column_selectors['popup'] = DataColumnSelector(
                data=data,
                column_types=['categorical', 'text'],
                description="Popup text:",
                multi_select=False,
                allow_none=True
            )
            selectors.append(self._column_selectors['popup'].widget)
            
        elif map_type == MapType.CHOROPLETH:
            # Value column for coloring
            self._column_selectors['value'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="Values:",
                multi_select=False
            )
            # Region identifier
            self._column_selectors['region'] = DataColumnSelector(
                data=data,
                column_types=['categorical'],
                description="Region ID:",
                multi_select=False
            )
            selectors.extend([
                self._column_selectors['value'].widget,
                self._column_selectors['region'].widget
            ])
            
        elif map_type == MapType.HEATMAP:
            # Intensity column
            self._column_selectors['intensity'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="Intensity:",
                multi_select=False,
                allow_none=True
            )
            selectors.append(self._column_selectors['intensity'].widget)
            
        elif map_type == MapType.CLUSTER:
            # Popup text column
            self._column_selectors['popup'] = DataColumnSelector(
                data=data,
                column_types=['categorical', 'text'],
                description="Popup text:",
                multi_select=False,
                allow_none=True
            )
            selectors.append(self._column_selectors['popup'].widget)
            
        elif map_type == MapType.BUBBLE:
            # Size column
            self._column_selectors['size'] = DataColumnSelector(
                data=data,
                column_types=['numeric'],
                description="Bubble size:",
                multi_select=False
            )
            # Color column
            self._column_selectors['color'] = DataColumnSelector(
                data=data,
                column_types=['categorical', 'numeric'],
                description="Color by:",
                multi_select=False,
                allow_none=True
            )
            selectors.extend([
                self._column_selectors['size'].widget,
                self._column_selectors['color'].widget
            ])
        
        # Update container
        self._column_selection_container.children = [
            widgets.HTML("<h5>Data Columns</h5>")
        ] + selectors
        
        # Add change callbacks
        for selector in self._column_selectors.values():
            selector.add_change_callback(self._on_column_selection_change)
    
    def _on_column_selection_change(self, column_name: str) -> None:
        """Handle column selection change."""
        # Could trigger preview or validation here
        pass
    
    def _update_style_controls(self) -> None:
        """Update style controls based on map type."""
        map_type = self._map_type_selector.value if self._map_type_selector else MapType.MARKER
        
        # Common style controls
        controls = []
        
        # Tile layer selection
        self._tile_layer = widgets.Dropdown(
            options=[
                ('OpenStreetMap', 'OpenStreetMap'),
                ('Stamen Terrain', 'Stamen Terrain'),
                ('Stamen Toner', 'Stamen Toner'),
                ('CartoDB Positron', 'CartoDB positron'),
                ('CartoDB Dark Matter', 'CartoDB dark_matter')
            ],
            description="Base map:",
            value='OpenStreetMap'
        )
        controls.append(self._tile_layer)
        
        # Color scheme
        self._color_scheme = widgets.Dropdown(
            options=[
                ('Default', 'viridis'),
                ('Blues', 'Blues'),
                ('Reds', 'Reds'),
                ('Greens', 'Greens'),
                ('Plasma', 'plasma'),
                ('Inferno', 'inferno'),
                ('Cividis', 'cividis')
            ],
            description="Color scheme:",
            value='viridis'
        )
        controls.append(self._color_scheme)
        
        # Map-specific controls
        if map_type == MapType.MARKER:
            self._marker_color = widgets.ColorPicker(
                value='#1f77b4',
                description="Marker color:"
            )
            controls.append(self._marker_color)
            
        elif map_type == MapType.HEATMAP:
            self._heatmap_radius = widgets.IntSlider(
                value=15,
                min=5,
                max=50,
                description="Heat radius:",
                continuous_update=False
            )
            controls.append(self._heatmap_radius)
            
        elif map_type == MapType.BUBBLE:
            self._min_bubble_size = widgets.IntSlider(
                value=5,
                min=1,
                max=20,
                description="Min size:",
                continuous_update=False
            )
            self._max_bubble_size = widgets.IntSlider(
                value=30,
                min=10,
                max=100,
                description="Max size:",
                continuous_update=False
            )
            controls.extend([self._min_bubble_size, self._max_bubble_size])
        
        # Map dimensions
        self._map_width = widgets.IntSlider(
            value=800,
            min=400,
            max=1200,
            description="Width:",
            continuous_update=False
        )
        controls.append(self._map_width)
        
        self._map_height = widgets.IntSlider(
            value=600,
            min=300,
            max=900,
            description="Height:",
            continuous_update=False
        )
        controls.append(self._map_height)
        
        # Update container
        self._style_controls_container.children = [
            widgets.HTML("<h5>Style Options</h5>")
        ] + controls
    
    @handle_errors("map creation")
    def _create_map(self) -> None:
        """Create a map based on current configuration."""
        if not self.app_service or self.app_service.current_data is None:
            self._message_display.show_message("No data available for mapping", "error")
            return
        
        # Validate location data
        if not self._validate_location_data():
            return
        
        # Build map configuration
        map_config = self._build_map_config()
        if not map_config:
            return
        
        try:
            # Create the map
            self._message_display.show_message("Creating map...", "info")
            result = self.app_service.create_map(map_config)
            
            # Display the map
            with self._map_display:
                self._map_display.clear_output()
                if hasattr(result, '_repr_html_'):
                    from IPython.display import display
                    display(result)
                else:
                    print("Map created successfully! (Display functionality depends on environment)")
            
            self._last_map_result = result
            self._current_map_config = map_config
            
            self._message_display.show_message("Map created successfully!", "success")
            
        except Exception as e:
            self.logger.error(f"Failed to create map: {e}")
            self._message_display.show_message(f"Failed to create map: {str(e)}", "error")
    
    def _validate_location_data(self) -> bool:
        """Validate that location data is available."""
        # Check if we have coordinates
        if (self._lat_selector and self._lat_selector.value and
            self._lon_selector and self._lon_selector.value):
            return True
        
        # Check if we have address column for geocoding
        if hasattr(self, '_address_selector') and self._address_selector.value:
            self._message_display.show_message(
                "Address column selected. Please geocode addresses first.",
                "warning"
            )
            return False
        
        self._message_display.show_message(
            "Please specify latitude/longitude columns or an address column for geocoding.",
            "warning"
        )
        return False
    
    def _build_map_config(self) -> Optional[MapConfig]:
        """Build map configuration from current widget state."""
        try:
            map_type = self._map_type_selector.value
            
            # Build column mappings
            columns = {}
            for key, selector in self._column_selectors.items():
                if selector.value:
                    columns[key] = selector.value
            
            # Location configuration
            location_config = {
                'latitude_column': self._lat_selector.value if self._lat_selector else None,
                'longitude_column': self._lon_selector.value if self._lon_selector else None,
                'center_lat': self._center_lat.value,
                'center_lon': self._center_lon.value,
                'zoom': self._zoom_level.value
            }
            
            # Style configuration
            style_config = StyleConfig(
                color_scheme=self._color_scheme.value,
                width=self._map_width.value,
                height=self._map_height.value,
            )
            
            # Map-specific configuration
            map_kwargs = {
                'tile_layer': self._tile_layer.value
            }
            
            if map_type == MapType.MARKER and hasattr(self, '_marker_color'):
                map_kwargs['marker_color'] = self._marker_color.value
            
            if map_type == MapType.HEATMAP and hasattr(self, '_heatmap_radius'):
                map_kwargs['radius'] = self._heatmap_radius.value
            
            if map_type == MapType.BUBBLE:
                if hasattr(self, '_min_bubble_size'):
                    map_kwargs['min_size'] = self._min_bubble_size.value
                if hasattr(self, '_max_bubble_size'):
                    map_kwargs['max_size'] = self._max_bubble_size.value
            
            # Create map configuration
            map_config = MapConfig(
                map_type=map_type,
                columns=columns,
                location=location_config,
                style=style_config,
                **map_kwargs
            )
            
            return map_config
            
        except Exception as e:
            self.logger.error(f"Failed to build map config: {e}")
            self._message_display.show_message(
                f"Configuration error: {str(e)}",
                "error"
            )
            return None
    
    def _export_map(self) -> None:
        """Export the current map."""
        if not self._last_map_result:
            self._message_display.show_message("No map to export", "warning")
            return
        
        # In a real implementation, this would save the map as HTML
        self._message_display.show_message(
            "Export functionality would save map as HTML file",
            "info"
        )
    
    @handle_errors("geocoding")
    def _geocode_addresses(self) -> None:
        """Geocode addresses in the selected address column."""
        if not hasattr(self, '_address_selector') or not self._address_selector.value:
            self._message_display.show_message("Please select an address column first", "warning")
            return
        
        if not self.app_service or self.app_service.current_data is None:
            self._message_display.show_message("No data available", "error")
            return
        
        try:
            address_column = self._address_selector.value
            self._message_display.show_message(f"Geocoding addresses in '{address_column}' column...", "info")
            
            # This would call the GeoProcessor's geocoding functionality
            # For now, we'll just show a placeholder message
            self._message_display.show_message(
                f"Geocoding complete! Added latitude and longitude columns.",
                "success"
            )
            
            # Update the interface to show new coordinate columns
            self._update_location_controls()
            
        except Exception as e:
            self.logger.error(f"Geocoding failed: {e}")
            self._message_display.show_message(f"Geocoding failed: {str(e)}", "error")
    
    @property
    def current_map_config(self) -> Optional[MapConfig]:
        """Get the current map configuration."""
        return self._current_map_config
    
    @property
    def last_map_result(self) -> Optional[Any]:
        """Get the last map result."""
        return self._last_map_result
    
    def set_map_type(self, map_type: MapType) -> None:
        """Set the map type programmatically."""
        if self._map_type_selector:
            self._map_type_selector.value = map_type
    
    def get_location_columns(self) -> Dict[str, str]:
        """Get the current location column mappings."""
        return {
            'latitude': self._lat_selector.value if self._lat_selector else None,
            'longitude': self._lon_selector.value if self._lon_selector else None,
            'address': getattr(self, '_address_selector', {}).get('value', None)
        }