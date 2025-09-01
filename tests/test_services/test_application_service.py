"""Unit tests for ApplicationService class."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

from dataviztest.services.application_service import ApplicationService
from dataviztest.core import DataProcessor, FilterEngine, VisualizationEngine, GeoProcessor
from dataviztest.services import StateManager, ValidationService
from dataviztest.models import (
    PlotConfig, PlotType, MapConfig, MapType, FilterSet, NumericFilter,
    FilterOperator, StyleConfig, LegendConfig
)
from dataviztest.infrastructure.exceptions import (
    DataProcessingError, FilterError, VisualizationError, GeospatialError
)


class TestApplicationService:
    """Test cases for ApplicationService."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for testing."""
        return {
            'data_processor': Mock(spec=DataProcessor),
            'filter_engine': Mock(spec=FilterEngine),
            'visualization_engine': Mock(spec=VisualizationEngine),
            'geo_processor': Mock(spec=GeoProcessor),
            'state_manager': Mock(spec=StateManager),
            'validation_service': Mock(spec=ValidationService)
        }
    
    @pytest.fixture
    def app_service(self, mock_components):
        """Create ApplicationService with mocked components."""
        return ApplicationService(
            data_processor=mock_components['data_processor'],
            filter_engine=mock_components['filter_engine'],
            visualization_engine=mock_components['visualization_engine'],
            geo_processor=mock_components['geo_processor'],
            state_manager=mock_components['state_manager'],
            validation_service=mock_components['validation_service']
        )
    
    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        return pd.DataFrame({
            'id': range(1, 101),
            'name': [f'Item_{i}' for i in range(1, 101)],
            'category': ['A', 'B', 'C'] * 33 + ['A'],
            'value': range(100, 200),
            'score': [i * 0.5 for i in range(100)],
            'latitude': [40.0 + i * 0.01 for i in range(100)],
            'longitude': [-74.0 + i * 0.01 for i in range(100)]
        })
    
    def test_initialization_default(self):
        """Test ApplicationService initialization with default components."""
        service = ApplicationService()
        
        assert service.data_processor is not None
        assert service.filter_engine is not None
        assert service.visualization_engine is not None
        assert service.geo_processor is not None
        assert service.state_manager is not None
        assert service.validation_service is not None
    
    def test_initialization_custom(self, mock_components):
        """Test ApplicationService initialization with custom components."""
        service = ApplicationService(**mock_components)
        
        assert service.data_processor == mock_components['data_processor']
        assert service.filter_engine == mock_components['filter_engine']
        assert service.visualization_engine == mock_components['visualization_engine']
        assert service.geo_processor == mock_components['geo_processor']
        assert service.state_manager == mock_components['state_manager']
        assert service.validation_service == mock_components['validation_service']
    
    def test_load_data_success(self, app_service, mock_components, sample_data):
        """Test successful data loading."""
        # Setup mocks
        mock_components['data_processor'].load_data.return_value = None
        mock_components['validation_service'].validate_data.return_value = {'is_valid': True}
        mock_components['state_manager'].update_state.return_value = None
        
        # Execute
        result = app_service.load_data(sample_data)
        
        # Verify
        mock_components['data_processor'].load_data.assert_called_once_with(sample_data)
        mock_components['validation_service'].validate_data.assert_called_once()
        mock_components['state_manager'].update_state.assert_called_once()
        assert result is None  # Success case returns None
    
    def test_load_data_validation_failure(self, app_service, mock_components, sample_data):
        """Test data loading with validation failure."""
        # Setup mocks
        mock_components['validation_service'].validate_data.return_value = {
            'is_valid': False,
            'errors': ['Invalid data format']
        }
        
        # Execute and verify
        with pytest.raises(DataProcessingError) as exc_info:
            app_service.load_data(sample_data)
        
        assert "Data validation failed" in str(exc_info.value)
        mock_components['data_processor'].load_data.assert_not_called()
    
    def test_load_data_processing_error(self, app_service, mock_components, sample_data):
        """Test data loading with processing error."""
        # Setup mocks
        mock_components['validation_service'].validate_data.return_value = {'is_valid': True}
        mock_components['data_processor'].load_data.side_effect = Exception("Processing failed")
        
        # Execute and verify
        with pytest.raises(DataProcessingError) as exc_info:
            app_service.load_data(sample_data)
        
        assert "Failed to load data" in str(exc_info.value)
    
    def test_apply_filters_success(self, app_service, mock_components, sample_data):
        """Test successful filter application."""
        # Setup
        filter_set = FilterSet(
            name="test_filter",
            filters=[
                NumericFilter(
                    column="value",
                    operator=FilterOperator.GREATER_THAN,
                    value=150
                )
            ]
        )
        filtered_data = sample_data[sample_data['value'] > 150]
        
        # Setup mocks
        mock_components['data_processor'].data = sample_data
        mock_components['filter_engine'].apply_filters.return_value = filtered_data
        mock_components['state_manager'].update_state.return_value = None
        
        # Execute
        result = app_service.apply_filters([filter_set])
        
        # Verify
        mock_components['filter_engine'].apply_filters.assert_called_once()
        mock_components['state_manager'].update_state.assert_called_once()
        pd.testing.assert_frame_equal(result, filtered_data)
    
    def test_apply_filters_no_data(self, app_service, mock_components):
        """Test filter application with no data loaded."""
        # Setup mocks
        mock_components['data_processor'].data = None
        
        # Execute and verify
        with pytest.raises(FilterError) as exc_info:
            app_service.apply_filters([])
        
        assert "No data available for filtering" in str(exc_info.value)
    
    def test_apply_filters_engine_error(self, app_service, mock_components, sample_data):
        """Test filter application with engine error."""
        # Setup
        filter_set = FilterSet(name="test_filter", filters=[])
        
        # Setup mocks
        mock_components['data_processor'].data = sample_data
        mock_components['filter_engine'].apply_filters.side_effect = Exception("Filter error")
        
        # Execute and verify
        with pytest.raises(FilterError) as exc_info:
            app_service.apply_filters([filter_set])
        
        assert "Failed to apply filters" in str(exc_info.value)
    
    def test_create_visualization_success(self, app_service, mock_components, sample_data):
        """Test successful visualization creation."""
        # Setup
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value', 'y': 'score'},
            title="Test Plot"
        )
        mock_plot = Mock()
        
        # Setup mocks
        mock_components['data_processor'].data = sample_data
        mock_components['visualization_engine'].create_plot.return_value = mock_plot
        mock_components['state_manager'].update_state.return_value = None
        
        # Execute
        result = app_service.create_visualization(plot_config)
        
        # Verify
        mock_components['visualization_engine'].create_plot.assert_called_once_with(
            sample_data, plot_config
        )
        mock_components['state_manager'].update_state.assert_called_once()
        assert result == mock_plot
    
    def test_create_visualization_no_data(self, app_service, mock_components):
        """Test visualization creation with no data."""
        # Setup
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value', 'y': 'score'}
        )
        
        # Setup mocks
        mock_components['data_processor'].data = None
        
        # Execute and verify
        with pytest.raises(VisualizationError) as exc_info:
            app_service.create_visualization(plot_config)
        
        assert "No data available for visualization" in str(exc_info.value)
    
    def test_create_visualization_engine_error(self, app_service, mock_components, sample_data):
        """Test visualization creation with engine error."""
        # Setup
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value', 'y': 'score'}
        )
        
        # Setup mocks
        mock_components['data_processor'].data = sample_data
        mock_components['visualization_engine'].create_plot.side_effect = Exception("Viz error")
        
        # Execute and verify
        with pytest.raises(VisualizationError) as exc_info:
            app_service.create_visualization(plot_config)
        
        assert "Failed to create visualization" in str(exc_info.value)
    
    def test_create_map_success(self, app_service, mock_components, sample_data):
        """Test successful map creation."""
        # Setup
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={
                'latitude_column': 'latitude',
                'longitude_column': 'longitude',
                'center_lat': 40.0,
                'center_lon': -74.0,
                'zoom': 10
            }
        )
        mock_map = Mock()
        
        # Setup mocks
        mock_components['data_processor'].data = sample_data
        mock_components['geo_processor'].create_map.return_value = mock_map
        mock_components['state_manager'].update_state.return_value = None
        
        # Execute
        result = app_service.create_map(map_config)
        
        # Verify
        mock_components['geo_processor'].create_map.assert_called_once_with(
            sample_data, map_config
        )
        mock_components['state_manager'].update_state.assert_called_once()
        assert result == mock_map
    
    def test_create_map_no_data(self, app_service, mock_components):
        """Test map creation with no data."""
        # Setup
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={'latitude_column': 'lat', 'longitude_column': 'lon'}
        )
        
        # Setup mocks
        mock_components['data_processor'].data = None
        
        # Execute and verify
        with pytest.raises(GeospatialError) as exc_info:
            app_service.create_map(map_config)
        
        assert "No data available for mapping" in str(exc_info.value)
    
    def test_create_map_processor_error(self, app_service, mock_components, sample_data):
        """Test map creation with processor error."""
        # Setup
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={'latitude_column': 'latitude', 'longitude_column': 'longitude'}
        )
        
        # Setup mocks
        mock_components['data_processor'].data = sample_data
        mock_components['geo_processor'].create_map.side_effect = Exception("Map error")
        
        # Execute and verify
        with pytest.raises(GeospatialError) as exc_info:
            app_service.create_map(map_config)
        
        assert "Failed to create map" in str(exc_info.value)
    
    def test_current_data_property(self, app_service, mock_components, sample_data):
        """Test current_data property."""
        # Setup mock
        mock_components['data_processor'].data = sample_data
        
        # Execute and verify
        result = app_service.current_data
        pd.testing.assert_frame_equal(result, sample_data)
    
    def test_current_data_property_none(self, app_service, mock_components):
        """Test current_data property when no data loaded."""
        # Setup mock
        mock_components['data_processor'].data = None
        
        # Execute and verify
        result = app_service.current_data
        assert result is None
    
    def test_current_state_property(self, app_service, mock_components):
        """Test current_state property."""
        # Setup mock
        mock_state = {'data_loaded': True, 'filters_applied': False}
        mock_components['state_manager'].current_state = mock_state
        
        # Execute and verify
        result = app_service.current_state
        assert result == mock_state
    
    def test_get_data_summary(self, app_service, mock_components):
        """Test get_data_summary method."""
        # Setup mock
        expected_summary = {
            'rows': 100,
            'columns': 5,
            'memory_usage': '1.2MB',
            'null_counts': {'col1': 0, 'col2': 5}
        }
        mock_components['data_processor'].get_data_quality_report.return_value = expected_summary
        
        # Execute
        result = app_service.get_data_summary()
        
        # Verify
        mock_components['data_processor'].get_data_quality_report.assert_called_once()
        assert result == expected_summary
    
    def test_validate_plot_config(self, app_service, mock_components):
        """Test validate_plot_config method."""
        # Setup
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value', 'y': 'score'}
        )
        expected_result = {'is_valid': True}
        mock_components['validation_service'].validate_plot_config.return_value = expected_result
        
        # Execute
        result = app_service.validate_plot_config(plot_config)
        
        # Verify
        mock_components['validation_service'].validate_plot_config.assert_called_once_with(plot_config)
        assert result == expected_result
    
    def test_validate_map_config(self, app_service, mock_components):
        """Test validate_map_config method."""
        # Setup
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={'latitude_column': 'lat', 'longitude_column': 'lon'}
        )
        expected_result = {'is_valid': True}
        mock_components['validation_service'].validate_map_config.return_value = expected_result
        
        # Execute
        result = app_service.validate_map_config(map_config)
        
        # Verify
        mock_components['validation_service'].validate_map_config.assert_called_once_with(map_config)
        assert result == expected_result