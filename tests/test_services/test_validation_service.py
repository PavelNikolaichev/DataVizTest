"""Unit tests for ValidationService class."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from typing import Any, Dict, List

from dataviztest.services.validation_service import ValidationService
from dataviztest.models import (
    PlotConfig, PlotType, MapConfig, MapType, FilterSet, NumericFilter,
    CategoricalFilter, FilterOperator, StyleConfig, LegendConfig
)
from dataviztest.infrastructure.exceptions import DataValidationError


class TestValidationService:
    """Test cases for ValidationService."""
    
    @pytest.fixture
    def validation_service(self):
        """Create ValidationService instance for testing."""
        return ValidationService()
    
    @pytest.fixture
    def valid_data(self):
        """Create valid test data."""
        return pd.DataFrame({
            'id': range(1, 101),
            'name': [f'Item_{i}' for i in range(1, 101)],
            'category': ['A', 'B', 'C'] * 33 + ['A'],
            'value': np.random.normal(100, 25, 100),
            'score': np.random.uniform(0, 100, 100),
            'latitude': np.random.uniform(40.0, 41.0, 100),
            'longitude': np.random.uniform(-74.5, -73.5, 100),
            'date': pd.date_range('2023-01-01', periods=100, freq='D'),
            'is_active': np.random.choice([True, False], 100)
        })
    
    @pytest.fixture
    def empty_data(self):
        """Create empty test data."""
        return pd.DataFrame()
    
    @pytest.fixture
    def data_with_nulls(self):
        """Create test data with null values."""
        data = pd.DataFrame({
            'id': [1, 2, None, 4, 5],
            'name': ['A', None, 'C', 'D', 'E'],
            'value': [10.0, 20.0, None, 40.0, 50.0],
            'category': ['X', 'Y', 'Z', None, 'X']
        })
        return data
    
    def test_validate_data_valid(self, validation_service, valid_data):
        """Test validation of valid data."""
        result = validation_service.validate_data(valid_data)
        
        assert result['is_valid'] is True
        assert 'errors' not in result or len(result['errors']) == 0
        assert 'warnings' in result
        assert result['summary']['total_rows'] == 100
        assert result['summary']['total_columns'] == 9
        assert result['summary']['memory_usage_mb'] > 0
    
    def test_validate_data_empty(self, validation_service, empty_data):
        """Test validation of empty data."""
        result = validation_service.validate_data(empty_data)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('empty' in error.lower() for error in result['errors'])
    
    def test_validate_data_none(self, validation_service):
        """Test validation of None data."""
        result = validation_service.validate_data(None)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('none' in error.lower() or 'null' in error.lower() for error in result['errors'])
    
    def test_validate_data_with_nulls(self, validation_service, data_with_nulls):
        """Test validation of data with null values."""
        result = validation_service.validate_data(data_with_nulls)
        
        assert result['is_valid'] is True  # Nulls are allowed but generate warnings
        assert 'warnings' in result
        assert len(result['warnings']) > 0
        assert result['data_quality']['null_counts']['id'] == 1
        assert result['data_quality']['null_counts']['name'] == 1
    
    def test_validate_data_large_dataset(self, validation_service):
        """Test validation warning for large dataset."""
        # Create large dataset
        large_data = pd.DataFrame({
            'id': range(100000),
            'value': range(100000)
        })
        
        result = validation_service.validate_data(large_data)
        
        assert result['is_valid'] is True
        assert 'warnings' in result
        # Should warn about large dataset
        assert any('large' in warning.lower() for warning in result['warnings'])
    
    def test_validate_data_high_memory_usage(self, validation_service):
        """Test validation warning for high memory usage."""
        # Create data with high memory usage
        high_memory_data = pd.DataFrame({
            'text_col': ['x' * 1000] * 10000,  # Large text column
            'id': range(10000)
        })
        
        result = validation_service.validate_data(high_memory_data)
        
        assert result['is_valid'] is True
        assert 'warnings' in result
        # Should warn about high memory usage
        assert any('memory' in warning.lower() for warning in result['warnings'])
    
    def test_validate_plot_config_valid_scatter(self, validation_service, valid_data):
        """Test validation of valid scatter plot configuration."""
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value', 'y': 'score'},
            title="Test Scatter Plot"
        )
        
        result = validation_service.validate_plot_config(plot_config, valid_data)
        
        assert result['is_valid'] is True
        assert 'errors' not in result or len(result['errors']) == 0
    
    def test_validate_plot_config_valid_bar(self, validation_service, valid_data):
        """Test validation of valid bar plot configuration."""
        plot_config = PlotConfig(
            plot_type=PlotType.BAR,
            columns={'x': 'category', 'y': 'value'},
            title="Test Bar Plot"
        )
        
        result = validation_service.validate_plot_config(plot_config, valid_data)
        
        assert result['is_valid'] is True
        assert 'errors' not in result or len(result['errors']) == 0
    
    def test_validate_plot_config_missing_columns(self, validation_service, valid_data):
        """Test validation of plot config with missing columns."""
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'nonexistent_column', 'y': 'score'},
            title="Test Plot"
        )
        
        result = validation_service.validate_plot_config(plot_config, valid_data)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('nonexistent_column' in error for error in result['errors'])
    
    def test_validate_plot_config_wrong_column_type(self, validation_service, valid_data):
        """Test validation of plot config with wrong column type."""
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'category', 'y': 'name'},  # Both should be numeric for scatter
            title="Test Plot"
        )
        
        result = validation_service.validate_plot_config(plot_config, valid_data)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('numeric' in error.lower() for error in result['errors'])
    
    def test_validate_plot_config_missing_required_columns(self, validation_service, valid_data):
        """Test validation of plot config missing required columns."""
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value'},  # Missing 'y' column for scatter plot
            title="Test Plot"
        )
        
        result = validation_service.validate_plot_config(plot_config, valid_data)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('required' in error.lower() for error in result['errors'])
    
    def test_validate_plot_config_histogram_valid(self, validation_service, valid_data):
        """Test validation of valid histogram configuration."""
        plot_config = PlotConfig(
            plot_type=PlotType.HISTOGRAM,
            columns={'x': 'value'},
            title="Test Histogram"
        )
        
        result = validation_service.validate_plot_config(plot_config, valid_data)
        
        assert result['is_valid'] is True
    
    def test_validate_plot_config_no_data(self, validation_service):
        """Test validation of plot config with no data."""
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value', 'y': 'score'}
        )
        
        result = validation_service.validate_plot_config(plot_config, None)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('data' in error.lower() for error in result['errors'])
    
    def test_validate_map_config_valid_marker(self, validation_service, valid_data):
        """Test validation of valid marker map configuration."""
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={
                'latitude_column': 'latitude',
                'longitude_column': 'longitude',
                'center_lat': 40.5,
                'center_lon': -74.0,
                'zoom': 10
            }
        )
        
        result = validation_service.validate_map_config(map_config, valid_data)
        
        assert result['is_valid'] is True
        assert 'errors' not in result or len(result['errors']) == 0
    
    def test_validate_map_config_missing_location_columns(self, validation_service, valid_data):
        """Test validation of map config with missing location columns."""
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={
                'latitude_column': 'nonexistent_lat',
                'longitude_column': 'longitude'
            }
        )
        
        result = validation_service.validate_map_config(map_config, valid_data)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('nonexistent_lat' in error for error in result['errors'])
    
    def test_validate_map_config_invalid_coordinates(self, validation_service):
        """Test validation of map config with invalid coordinate values."""
        # Create data with invalid coordinates
        invalid_data = pd.DataFrame({
            'latitude': [200, -200, 45],  # Invalid latitude values
            'longitude': [-74, 181, -75]  # Invalid longitude value
        })
        
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={
                'latitude_column': 'latitude',
                'longitude_column': 'longitude'
            }
        )
        
        result = validation_service.validate_map_config(map_config, invalid_data)
        
        assert 'warnings' in result
        assert any('coordinate' in warning.lower() or 'latitude' in warning.lower() 
                  for warning in result['warnings'])
    
    def test_validate_map_config_no_location_info(self, validation_service, valid_data):
        """Test validation of map config without location information."""
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={}
        )
        
        result = validation_service.validate_map_config(map_config, valid_data)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('location' in error.lower() for error in result['errors'])
    
    def test_validate_map_config_choropleth(self, validation_service, valid_data):
        """Test validation of choropleth map configuration."""
        map_config = MapConfig(
            map_type=MapType.CHOROPLETH,
            columns={'value': 'score', 'region': 'category'},
            location={'latitude_column': 'latitude', 'longitude_column': 'longitude'}
        )
        
        result = validation_service.validate_map_config(map_config, valid_data)
        
        assert result['is_valid'] is True
    
    def test_validate_filter_set_valid_numeric(self, validation_service, valid_data):
        """Test validation of valid numeric filter set."""
        filter_set = FilterSet(
            name="test_filter",
            filters=[
                NumericFilter(
                    column="value",
                    operator=FilterOperator.GREATER_THAN,
                    value=50
                )
            ]
        )
        
        result = validation_service.validate_filter_set(filter_set, valid_data)
        
        assert result['is_valid'] is True
        assert 'errors' not in result or len(result['errors']) == 0
    
    def test_validate_filter_set_valid_categorical(self, validation_service, valid_data):
        """Test validation of valid categorical filter set."""
        filter_set = FilterSet(
            name="test_filter",
            filters=[
                CategoricalFilter(
                    column="category",
                    operator=FilterOperator.IN,
                    values=['A', 'B']
                )
            ]
        )
        
        result = validation_service.validate_filter_set(filter_set, valid_data)
        
        assert result['is_valid'] is True
    
    def test_validate_filter_set_missing_column(self, validation_service, valid_data):
        """Test validation of filter set with missing column."""
        filter_set = FilterSet(
            name="test_filter",
            filters=[
                NumericFilter(
                    column="nonexistent_column",
                    operator=FilterOperator.GREATER_THAN,
                    value=50
                )
            ]
        )
        
        result = validation_service.validate_filter_set(filter_set, valid_data)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('nonexistent_column' in error for error in result['errors'])
    
    def test_validate_filter_set_wrong_column_type(self, validation_service, valid_data):
        """Test validation of filter set with wrong column type."""
        filter_set = FilterSet(
            name="test_filter",
            filters=[
                NumericFilter(
                    column="name",  # Text column used for numeric filter
                    operator=FilterOperator.GREATER_THAN,
                    value=50
                )
            ]
        )
        
        result = validation_service.validate_filter_set(filter_set, valid_data)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('numeric' in error.lower() for error in result['errors'])
    
    def test_validate_filter_set_empty_filters(self, validation_service, valid_data):
        """Test validation of filter set with no filters."""
        filter_set = FilterSet(
            name="empty_filter",
            filters=[]
        )
        
        result = validation_service.validate_filter_set(filter_set, valid_data)
        
        assert result['is_valid'] is False
        assert 'errors' in result
        assert any('no filters' in error.lower() for error in result['errors'])
    
    def test_get_column_types(self, validation_service, valid_data):
        """Test getting column types from data."""
        result = validation_service.get_column_types(valid_data)
        
        assert 'numeric' in result
        assert 'categorical' in result
        assert 'datetime' in result
        assert 'boolean' in result
        
        assert 'value' in result['numeric']
        assert 'score' in result['numeric']
        assert 'category' in result['categorical']
        assert 'name' in result['categorical']
        assert 'date' in result['datetime']
        assert 'is_active' in result['boolean']
    
    def test_get_column_types_empty_data(self, validation_service, empty_data):
        """Test getting column types from empty data."""
        result = validation_service.get_column_types(empty_data)
        
        assert result['numeric'] == []
        assert result['categorical'] == []
        assert result['datetime'] == []
        assert result['boolean'] == []
    
    def test_validate_column_compatibility_compatible(self, validation_service, valid_data):
        """Test column compatibility validation for compatible columns."""
        result = validation_service.validate_column_compatibility(
            data=valid_data,
            column='value',
            expected_type='numeric'
        )
        
        assert result['is_compatible'] is True
        assert 'errors' not in result or len(result['errors']) == 0
    
    def test_validate_column_compatibility_incompatible(self, validation_service, valid_data):
        """Test column compatibility validation for incompatible columns."""
        result = validation_service.validate_column_compatibility(
            data=valid_data,
            column='name',
            expected_type='numeric'
        )
        
        assert result['is_compatible'] is False
        assert 'errors' in result
        assert any('not compatible' in error.lower() for error in result['errors'])
    
    def test_validate_column_compatibility_missing_column(self, validation_service, valid_data):
        """Test column compatibility validation for missing column."""
        result = validation_service.validate_column_compatibility(
            data=valid_data,
            column='nonexistent',
            expected_type='numeric'
        )
        
        assert result['is_compatible'] is False
        assert 'errors' in result
        assert any('not found' in error.lower() for error in result['errors'])
    
    def test_get_data_quality_report(self, validation_service, data_with_nulls):
        """Test getting data quality report."""
        result = validation_service.get_data_quality_report(data_with_nulls)
        
        assert 'summary' in result
        assert 'null_counts' in result
        assert 'duplicate_rows' in result
        assert 'column_types' in result
        
        assert result['null_counts']['id'] == 1
        assert result['null_counts']['name'] == 1
        assert result['summary']['total_rows'] == 5
        assert result['summary']['total_columns'] == 4
    
    def test_check_memory_usage_normal(self, validation_service, valid_data):
        """Test memory usage check for normal data."""
        usage_mb = validation_service._check_memory_usage(valid_data)
        
        assert isinstance(usage_mb, float)
        assert usage_mb > 0
        assert usage_mb < 100  # Should be small for test data
    
    def test_validate_coordinate_values_valid(self, validation_service):
        """Test coordinate validation for valid values."""
        valid_coords = pd.DataFrame({
            'lat': [40.0, 41.0, 39.0],
            'lon': [-74.0, -73.0, -75.0]
        })
        
        lat_issues, lon_issues = validation_service._validate_coordinate_values(
            valid_coords, 'lat', 'lon'
        )
        
        assert lat_issues == 0
        assert lon_issues == 0
    
    def test_validate_coordinate_values_invalid(self, validation_service):
        """Test coordinate validation for invalid values."""
        invalid_coords = pd.DataFrame({
            'lat': [200, -100, 45],  # Invalid latitude
            'lon': [-74, 200, -75]   # Invalid longitude
        })
        
        lat_issues, lon_issues = validation_service._validate_coordinate_values(
            invalid_coords, 'lat', 'lon'
        )
        
        assert lat_issues == 2  # Two invalid latitude values
        assert lon_issues == 1  # One invalid longitude value