"""Geospatial processing functionality for DataVizTest application.

This module provides geospatial operations including geocoding, coordinate
transformation, and map visualization using geopandas and folium.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple, Union
import warnings

import pandas as pd
import numpy as np
import folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderQuotaExceeded

try:
    import geopandas as gpd
    from shapely.geometry import Point, Polygon
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    warnings.warn("GeoPandas not available. Some geospatial features will be limited.")

from ..infrastructure import (
    GeospatialError,
    GeocodingError,
    MappingError,
    get_logger,
    log_performance,
    handle_errors,
    get_settings,
)
from ..models import MapConfig, MapType


class GeoProcessor:
    """Geospatial data processor for DataVizTest application."""
    
    def __init__(self):
        """Initialize the geo processor."""
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        
        # Initialize geocoder with rate limiting
        self.geocoder = Nominatim(user_agent="DataVizTest")
        self.geocode = RateLimiter(
            self.geocoder.geocode,
            min_delay_seconds=1/self.settings.geocoding_rate_limit
        )
        
        # Cache for geocoding results
        self._geocoding_cache: Dict[str, Tuple[float, float]] = {}
    
    @log_performance
    @handle_errors("geocoding")
    def geocode_addresses(
        self, 
        addresses: Union[pd.Series, List[str]], 
        use_cache: bool = True
    ) -> pd.DataFrame:
        """Geocode a list of addresses to coordinates.
        
        Args:
            addresses: Series or list of address strings
            use_cache: Whether to use cached results
            
        Returns:
            DataFrame with original address, latitude, longitude, and success status
        """
        if isinstance(addresses, pd.Series):
            address_list = addresses.dropna().unique().tolist()
        else:
            address_list = list(set([addr for addr in addresses if addr]))
        
        results = []
        
        for address in address_list:
            if use_cache and address in self._geocoding_cache:
                lat, lon = self._geocoding_cache[address]
                results.append({
                    'address': address,
                    'latitude': lat,
                    'longitude': lon,
                    'geocoded': True,
                    'error': None
                })
                continue
            
            try:
                location = self.geocode(address)
                if location:
                    lat, lon = location.latitude, location.longitude
                    if use_cache:
                        self._geocoding_cache[address] = (lat, lon)
                    
                    results.append({
                        'address': address,
                        'latitude': lat,
                        'longitude': lon,
                        'geocoded': True,
                        'error': None
                    })
                else:
                    results.append({
                        'address': address,
                        'latitude': None,
                        'longitude': None,
                        'geocoded': False,
                        'error': 'Address not found'
                    })
                    
            except (GeocoderTimedOut, GeocoderQuotaExceeded) as e:
                self.logger.warning(f"Geocoding failed for '{address}': {e}")
                results.append({
                    'address': address,
                    'latitude': None,
                    'longitude': None,
                    'geocoded': False,
                    'error': str(e)
                })
            except Exception as e:
                self.logger.error(f"Unexpected geocoding error for '{address}': {e}")
                results.append({
                    'address': address,
                    'latitude': None,
                    'longitude': None,
                    'geocoded': False,
                    'error': f"Geocoding error: {e}"
                })
        
        result_df = pd.DataFrame(results)
        
        success_rate = (result_df['geocoded'].sum() / len(result_df)) * 100
        self.logger.info(
            f"Geocoded {len(address_list)} addresses with {success_rate:.1f}% success rate"
        )
        
        return result_df
    
    @handle_errors("coordinate validation")
    def validate_coordinates(
        self, 
        df: pd.DataFrame, 
        lat_col: str, 
        lon_col: str
    ) -> pd.DataFrame:
        """Validate latitude and longitude coordinates.
        
        Args:
            df: DataFrame with coordinate columns
            lat_col: Latitude column name
            lon_col: Longitude column name
            
        Returns:
            DataFrame with validation results
        """
        if lat_col not in df.columns or lon_col not in df.columns:
            raise GeospatialError(f"Coordinate columns not found: {lat_col}, {lon_col}")
        
        validated_df = df.copy()
        
        # Check for valid coordinate ranges
        valid_lat = (df[lat_col] >= -90) & (df[lat_col] <= 90)
        valid_lon = (df[lon_col] >= -180) & (df[lon_col] <= 180)
        valid_coords = valid_lat & valid_lon & df[lat_col].notna() & df[lon_col].notna()
        
        validated_df['valid_coordinates'] = valid_coords
        
        invalid_count = (~valid_coords).sum()
        if invalid_count > 0:
            self.logger.warning(f"Found {invalid_count} invalid coordinates")
        
        return validated_df
    
    @handle_errors("coordinate conversion")
    def create_geopoints(
        self, 
        df: pd.DataFrame, 
        lat_col: str, 
        lon_col: str
    ) -> pd.Series:
        """Create Shapely Point geometries from coordinates.
        
        Args:
            df: DataFrame with coordinate columns
            lat_col: Latitude column name
            lon_col: Longitude column name
            
        Returns:
            Series of Point geometries
        """
        if not GEOPANDAS_AVAILABLE:
            raise GeospatialError("GeoPandas is required for geometric operations")
        
        # Validate coordinates first
        validated_df = self.validate_coordinates(df, lat_col, lon_col)
        
        def create_point(row):
            if row['valid_coordinates']:
                return Point(row[lon_col], row[lat_col])
            else:
                return None
        
        return validated_df.apply(create_point, axis=1)
    
    @log_performance
    @handle_errors("map creation")
    def create_map(
        self, 
        data: pd.DataFrame, 
        config: MapConfig
    ) -> folium.Map:
        """Create a folium map with the given data and configuration.
        
        Args:
            data: DataFrame with geospatial data
            config: Map configuration
            
        Returns:
            Folium map object
        """
        # Determine map center
        center_lat, center_lon = self._determine_map_center(data, config)
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=config.zoom_level,
            tiles=config.map_style
        )
        
        # Add data based on map type
        if config.map_type == MapType.SCATTER_MAP:
            self._add_scatter_markers(m, data, config)
        elif config.map_type == MapType.HEATMAP:
            self._add_heatmap(m, data, config)
        elif config.map_type == MapType.BUBBLE_MAP:
            self._add_bubble_markers(m, data, config)
        elif config.map_type == MapType.CHOROPLETH:
            self._add_choropleth(m, data, config)
        elif config.map_type == MapType.LINE_MAP:
            self._add_line_features(m, data, config)
        else:
            raise MappingError(f"Unsupported map type: {config.map_type}")
        
        # Add title
        if config.title:
            title_html = f'''
                <h3 align="center" style="font-size:20px"><b>{config.title}</b></h3>
            '''
            m.get_root().html.add_child(folium.Element(title_html))
        
        return m
    
    def _determine_map_center(
        self, 
        data: pd.DataFrame, 
        config: MapConfig
    ) -> Tuple[float, float]:
        """Determine the center point for the map.
        
        Args:
            data: DataFrame with geospatial data
            config: Map configuration
            
        Returns:
            Tuple of (latitude, longitude) for map center
        """
        # Use explicit center if provided
        if config.center_lat is not None and config.center_lon is not None:
            return config.center_lat, config.center_lon
        
        # Calculate center from data
        if config.latitude_column and config.longitude_column:
            lat_col = config.latitude_column
            lon_col = config.longitude_column
            
            if lat_col in data.columns and lon_col in data.columns:
                # Remove invalid coordinates
                valid_data = data.dropna(subset=[lat_col, lon_col])
                valid_data = valid_data[
                    (valid_data[lat_col] >= -90) & (valid_data[lat_col] <= 90) &
                    (valid_data[lon_col] >= -180) & (valid_data[lon_col] <= 180)
                ]
                
                if not valid_data.empty:
                    center_lat = valid_data[lat_col].mean()
                    center_lon = valid_data[lon_col].mean()
                    return center_lat, center_lon
        
        # Default center (world center)
        return 0.0, 0.0
    
    def _add_scatter_markers(
        self, 
        m: folium.Map, 
        data: pd.DataFrame, 
        config: MapConfig
    ) -> None:
        """Add scatter markers to the map.
        
        Args:
            m: Folium map object
            data: DataFrame with data
            config: Map configuration
        """
        if not config.latitude_column or not config.longitude_column:
            raise MappingError("Latitude and longitude columns required for scatter map")
        
        lat_col = config.latitude_column
        lon_col = config.longitude_column
        
        # Validate and filter data
        valid_data = self.validate_coordinates(data, lat_col, lon_col)
        valid_data = valid_data[valid_data['valid_coordinates']]
        
        for idx, row in valid_data.iterrows():
            # Create popup content
            popup_content = self._create_popup_content(row, config)
            
            # Determine marker color
            color = 'blue'
            if config.value_column and config.value_column in row:
                # Color based on value (simplified)
                value = row[config.value_column]
                if isinstance(value, (int, float)):
                    # Use green for high values, red for low values
                    normalized_value = (value - valid_data[config.value_column].min()) / \
                                     (valid_data[config.value_column].max() - valid_data[config.value_column].min())
                    if normalized_value > 0.7:
                        color = 'green'
                    elif normalized_value < 0.3:
                        color = 'red'
                    else:
                        color = 'orange'
            
            folium.Marker(
                location=[row[lat_col], row[lon_col]],
                popup=popup_content,
                icon=folium.Icon(color=color)
            ).add_to(m)
    
    def _add_bubble_markers(
        self, 
        m: folium.Map, 
        data: pd.DataFrame, 
        config: MapConfig
    ) -> None:
        """Add bubble markers to the map.
        
        Args:
            m: Folium map object
            data: DataFrame with data
            config: Map configuration
        """
        if not config.latitude_column or not config.longitude_column:
            raise MappingError("Latitude and longitude columns required for bubble map")
        
        if not config.size_column:
            raise MappingError("Size column required for bubble map")
        
        lat_col = config.latitude_column
        lon_col = config.longitude_column
        size_col = config.size_column
        
        # Validate and filter data
        valid_data = self.validate_coordinates(data, lat_col, lon_col)
        valid_data = valid_data[valid_data['valid_coordinates']]
        
        # Normalize sizes
        if size_col in valid_data.columns:
            min_size = valid_data[size_col].min()
            max_size = valid_data[size_col].max()
            size_range = max_size - min_size
            
            for idx, row in valid_data.iterrows():
                # Create popup content
                popup_content = self._create_popup_content(row, config)
                
                # Calculate bubble size (5-30 pixel radius)
                if size_range > 0:
                    normalized_size = (row[size_col] - min_size) / size_range
                    radius = 5 + (normalized_size * 25)
                else:
                    radius = 15
                
                folium.CircleMarker(
                    location=[row[lat_col], row[lon_col]],
                    radius=radius,
                    popup=popup_content,
                    fillOpacity=0.6
                ).add_to(m)
    
    def _add_heatmap(
        self, 
        m: folium.Map, 
        data: pd.DataFrame, 
        config: MapConfig
    ) -> None:
        """Add heatmap to the map.
        
        Args:
            m: Folium map object
            data: DataFrame with data
            config: Map configuration
        """
        try:
            from folium.plugins import HeatMap
        except ImportError:
            raise MappingError("HeatMap plugin not available")
        
        if not config.latitude_column or not config.longitude_column:
            raise MappingError("Latitude and longitude columns required for heatmap")
        
        lat_col = config.latitude_column
        lon_col = config.longitude_column
        
        # Validate and filter data
        valid_data = self.validate_coordinates(data, lat_col, lon_col)
        valid_data = valid_data[valid_data['valid_coordinates']]
        
        # Prepare heatmap data
        if config.value_column and config.value_column in valid_data.columns:
            # Use values for intensity
            heat_data = valid_data[[lat_col, lon_col, config.value_column]].values.tolist()
        else:
            # Use count for intensity
            heat_data = valid_data[[lat_col, lon_col]].values.tolist()
        
        HeatMap(heat_data).add_to(m)
    
    def _add_choropleth(
        self, 
        m: folium.Map, 
        data: pd.DataFrame, 
        config: MapConfig
    ) -> None:
        """Add choropleth to the map.
        
        Args:
            m: Folium map object
            data: DataFrame with data
            config: Map configuration
        """
        if not GEOPANDAS_AVAILABLE:
            raise MappingError("GeoPandas required for choropleth maps")
        
        # This is a simplified implementation
        # In practice, you'd need proper geospatial boundaries
        self.logger.warning("Choropleth mapping requires proper geospatial boundaries")
    
    def _add_line_features(
        self, 
        m: folium.Map, 
        data: pd.DataFrame, 
        config: MapConfig
    ) -> None:
        """Add line features to the map.
        
        Args:
            m: Folium map object
            data: DataFrame with data
            config: Map configuration
        """
        # This is a simplified implementation for line features
        self.logger.warning("Line mapping is not fully implemented yet")
    
    def _create_popup_content(self, row: pd.Series, config: MapConfig) -> str:
        """Create popup content for a marker.
        
        Args:
            row: Data row
            config: Map configuration
            
        Returns:
            HTML popup content
        """
        content = []
        
        # Add coordinates
        if config.latitude_column and config.longitude_column:
            lat = row.get(config.latitude_column, 'N/A')
            lon = row.get(config.longitude_column, 'N/A')
            content.append(f"<b>Location:</b> {lat:.4f}, {lon:.4f}")
        
        # Add configured popup columns
        for col in config.popup_columns:
            if col in row:
                value = row[col]
                content.append(f"<b>{col}:</b> {value}")
        
        # Add value column if specified
        if config.value_column and config.value_column in row:
            value = row[config.value_column]
            content.append(f"<b>{config.value_column}:</b> {value}")
        
        return "<br>".join(content)
    
    def get_geocoding_cache_stats(self) -> Dict[str, int]:
        """Get geocoding cache statistics.
        
        Returns:
            Cache statistics
        """
        return {
            "cached_addresses": len(self._geocoding_cache),
            "cache_size_mb": len(str(self._geocoding_cache)) / (1024 * 1024)
        }
    
    def clear_geocoding_cache(self) -> None:
        """Clear the geocoding cache."""
        self._geocoding_cache.clear()
        self.logger.debug("Geocoding cache cleared")