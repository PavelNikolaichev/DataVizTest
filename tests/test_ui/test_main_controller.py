"""Unit tests for MainUIController class."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List

import ipywidgets as widgets

from dataviztest.ui.main_controller import MainUIController, create_interface
from dataviztest.services import ApplicationService
from dataviztest.models import PlotConfig, PlotType, MapConfig, MapType, FilterSet
from dataviztest.ui.widgets import FilterWidget, PlottingWidget, MappingWidget


class TestMainUIController:
    """Test cases for MainUIController."""
    
    @pytest.fixture
    def mock_app_service(self):
        """Create mock ApplicationService for testing."""
        mock_service = Mock(spec=ApplicationService)
        mock_service.current_data = None
        mock_service.current_state = {'data_loaded': False}
        mock_service.state_manager = Mock()
        return mock_service
    
    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        return pd.DataFrame({
            'id': range(1, 51),
            'name': [f'Item_{i}' for i in range(1, 51)],
            'category': ['A', 'B', 'C'] * 16 + ['A', 'B'],
            'value': range(50, 100),
            'score': [i * 0.5 for i in range(50)],
            'latitude': [40.0 + i * 0.01 for i in range(50)],
            'longitude': [-74.0 + i * 0.01 for i in range(50)]
        })
    
    def test_initialization_default(self):
        """Test MainUIController initialization with default parameters."""
        with patch('dataviztest.ui.main_controller.ApplicationService'):
            controller = MainUIController(auto_display=False)
            
            assert controller.app_service is not None
            assert controller._initialized is False
            assert controller._main_widget is None
    
    def test_initialization_custom_service(self, mock_app_service):
        """Test MainUIController initialization with custom app service."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        
        assert controller.app_service == mock_app_service
        assert controller._initialized is False
    
    @patch('dataviztest.ui.main_controller.FilterWidget')
    @patch('dataviztest.ui.main_controller.PlottingWidget')
    @patch('dataviztest.ui.main_controller.MappingWidget')
    def test_create_interface(self, mock_mapping, mock_plotting, mock_filter, mock_app_service):
        """Test interface creation."""
        # Setup mocks
        mock_filter.return_value = Mock()
        mock_plotting.return_value = Mock()
        mock_mapping.return_value = Mock()
        
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._create_interface()
        
        assert controller._initialized is True
        assert controller._main_widget is not None
        assert controller._filter_widget is not None
        assert controller._plotting_widget is not None
        assert controller._mapping_widget is not None
        assert controller._message_display is not None
    
    def test_create_data_panel(self, mock_app_service):
        """Test data panel creation."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        
        data_panel = controller._create_data_panel()
        
        assert isinstance(data_panel, widgets.Widget)
        assert controller._file_upload is not None
        assert controller._data_info is not None
        assert controller._manual_data_input is not None
    
    def test_update_data_info_no_data(self, mock_app_service):
        """Test data info update with no data."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._create_data_panel()
        
        controller._update_data_info()
        
        assert 'No data loaded' in controller._data_info.value
    
    def test_update_data_info_with_data(self, mock_app_service, sample_data):
        """Test data info update with data."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._create_data_panel()
        controller._current_data = sample_data
        
        controller._update_data_info()
        
        info_value = controller._data_info.value
        assert 'Dataset Overview' in info_value
        assert '50' in info_value  # Row count
        assert '7' in info_value   # Column count
    
    def test_load_sample_data(self, mock_app_service):
        """Test loading sample data."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._create_data_panel()
        
        # Mock the message display
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        controller._load_sample_data()
        
        # Verify sample data was loaded
        assert controller._current_data is not None
        assert len(controller._current_data) == 100
        mock_app_service.load_data.assert_called_once()
        controller._message_display.show_message.assert_called()
    
    def test_load_manual_data_success(self, mock_app_service):
        """Test loading manual data successfully."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._create_data_panel()
        
        # Setup manual input
        csv_data = "id,name,value\n1,A,10\n2,B,20\n3,C,30"
        controller._manual_data_input.value = csv_data
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        controller._load_manual_data()
        
        # Verify data was loaded
        assert controller._current_data is not None
        assert len(controller._current_data) == 3
        assert list(controller._current_data.columns) == ['id', 'name', 'value']
        mock_app_service.load_data.assert_called_once()
        controller._message_display.show_message.assert_called()
    
    def test_load_manual_data_empty_input(self, mock_app_service):
        """Test loading manual data with empty input."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._create_data_panel()
        
        controller._manual_data_input.value = ""
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        controller._load_manual_data()
        
        # Verify warning was shown
        controller._message_display.show_message.assert_called_with(
            "Please paste some data first", "warning"
        )
        mock_app_service.load_data.assert_not_called()
    
    def test_load_manual_data_invalid_csv(self, mock_app_service):
        """Test loading manual data with invalid CSV."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._create_data_panel()
        
        controller._manual_data_input.value = "invalid,csv,data\nno,matching"
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        controller._load_manual_data()
        
        # Verify error was shown
        controller._message_display.show_message.assert_called()
        call_args = controller._message_display.show_message.call_args[0]
        assert "Failed to load data" in call_args[0]
        assert call_args[1] == "error"
    
    def test_file_upload_csv(self, mock_app_service):
        """Test file upload with CSV data."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._create_data_panel()
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        # Mock file upload
        csv_content = b"id,name,value\n1,A,10\n2,B,20"
        file_data = {
            'test.csv': {
                'content': csv_content,
                'metadata': {'name': 'test.csv'}
            }
        }
        
        change = {'new': file_data}
        
        with patch('pandas.read_csv') as mock_read_csv:
            mock_df = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B'], 'value': [10, 20]})
            mock_read_csv.return_value = mock_df
            
            controller._on_file_upload(change)
            
            # Verify data was loaded
            assert controller._current_data is not None
            mock_app_service.load_data.assert_called_once()
            controller._message_display.show_message.assert_called()
    
    def test_file_upload_unsupported_format(self, mock_app_service):
        """Test file upload with unsupported format."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._create_data_panel()
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        # Mock file upload with unsupported format
        file_data = {
            'test.txt': {
                'content': b"some text content",
                'metadata': {'name': 'test.txt'}
            }
        }
        
        change = {'new': file_data}
        controller._on_file_upload(change)
        
        # Verify error was shown
        controller._message_display.show_message.assert_called()
        call_args = controller._message_display.show_message.call_args[0]
        assert "Failed to load file" in call_args[0]
        assert call_args[1] == "error"
    
    def test_clear_data(self, mock_app_service):
        """Test clearing data."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        # Set some data first
        controller._current_data = pd.DataFrame({'a': [1, 2, 3]})
        
        controller._clear_data()
        
        assert controller._current_data is None
        controller._message_display.show_message.assert_called_with("Data cleared", "info")
    
    def test_refresh_data(self, mock_app_service):
        """Test refreshing data."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        controller._refresh_data()
        
        controller._message_display.show_message.assert_called_with("Data refreshed", "info")
    
    def test_export_data_no_data(self, mock_app_service):
        """Test exporting data when no data is available."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        controller._export_data()
        
        controller._message_display.show_message.assert_called_with(
            "No data to export", "warning"
        )
    
    def test_export_data_with_data(self, mock_app_service, sample_data):
        """Test exporting data when data is available."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._current_data = sample_data
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        controller._export_data()
        
        controller._message_display.show_message.assert_called()
        call_args = controller._message_display.show_message.call_args[0]
        assert "Export functionality" in call_args[0]
        assert call_args[1] == "info"
    
    def test_load_data_programmatically(self, mock_app_service, sample_data):
        """Test loading data programmatically."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        controller.load_data(sample_data)
        
        assert controller._current_data is not None
        pd.testing.assert_frame_equal(controller._current_data, sample_data)
        mock_app_service.load_data.assert_called_once_with(sample_data)
        controller._message_display.show_message.assert_called()
    
    def test_get_current_data(self, mock_app_service, sample_data):
        """Test getting current data."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        
        # Initially no data
        assert controller.get_current_data() is None
        
        # After loading data
        controller._current_data = sample_data
        result = controller.get_current_data()
        pd.testing.assert_frame_equal(result, sample_data)
    
    def test_create_plot_programmatically(self, mock_app_service):
        """Test creating plot programmatically."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value', 'y': 'score'}
        )
        
        mock_result = Mock()
        mock_app_service.create_visualization.return_value = mock_result
        
        result = controller.create_plot(plot_config)
        
        assert result == mock_result
        mock_app_service.create_visualization.assert_called_once_with(plot_config)
    
    def test_create_map_programmatically(self, mock_app_service):
        """Test creating map programmatically."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={'latitude_column': 'lat', 'longitude_column': 'lon'}
        )
        
        mock_result = Mock()
        mock_app_service.create_map.return_value = mock_result
        
        result = controller.create_map(map_config)
        
        assert result == mock_result
        mock_app_service.create_map.assert_called_once_with(map_config)
    
    def test_apply_filters_programmatically(self, mock_app_service):
        """Test applying filters programmatically."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        
        filter_set = FilterSet(name="test_filter", filters=[])
        mock_result = pd.DataFrame({'filtered': [1, 2, 3]})
        mock_app_service.apply_filters.return_value = mock_result
        
        result = controller.apply_filters(filter_set)
        
        pd.testing.assert_frame_equal(result, mock_result)
        mock_app_service.apply_filters.assert_called_once_with([filter_set])
    
    def test_widget_property(self, mock_app_service):
        """Test widget property."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        
        # Before initialization
        assert controller.widget is None
        
        # After initialization
        with patch.object(controller, '_create_interface'):
            controller._main_widget = Mock()
            assert controller.widget == controller._main_widget
    
    def test_is_initialized_property(self, mock_app_service):
        """Test is_initialized property."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        
        assert controller.is_initialized is False
        
        controller._initialized = True
        assert controller.is_initialized is True
    
    @patch('dataviztest.ui.main_controller.display')
    def test_display_method(self, mock_display, mock_app_service):
        """Test display method."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        
        # Mock the interface creation
        mock_widget = Mock()
        controller._main_widget = mock_widget
        controller._initialized = True
        
        controller.display()
        
        mock_display.assert_called_once_with(mock_widget)
    
    def test_on_state_change(self, mock_app_service):
        """Test state change handler."""
        controller = MainUIController(
            app_service=mock_app_service,
            auto_display=False
        )
        controller._message_display = Mock()
        controller._message_display.show_message = Mock()
        
        # Mock state
        mock_state = {'data_loaded': True}
        
        controller._on_state_change(mock_state)
        
        controller._message_display.show_message.assert_called_with(
            "Application state updated", "info"
        )


class TestCreateInterface:
    """Test cases for create_interface convenience function."""
    
    @patch('dataviztest.ui.main_controller.MainUIController')
    def test_create_interface_no_data_auto_display(self, mock_controller_class):
        """Test create_interface function without data and auto display."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        
        result = create_interface()
        
        mock_controller_class.assert_called_once_with(auto_display=True)
        mock_controller.display.assert_called_once()
        assert result == mock_controller
    
    @patch('dataviztest.ui.main_controller.MainUIController')
    def test_create_interface_with_data_no_display(self, mock_controller_class):
        """Test create_interface function with data and no auto display."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        
        sample_data = pd.DataFrame({'a': [1, 2, 3]})
        
        result = create_interface(data=sample_data, auto_display=False)
        
        mock_controller_class.assert_called_once_with(auto_display=False)
        mock_controller.load_data.assert_called_once_with(sample_data)
        mock_controller.display.assert_not_called()
        assert result == mock_controller
    
    @patch('dataviztest.ui.main_controller.MainUIController')
    def test_create_interface_with_data_auto_display(self, mock_controller_class):
        """Test create_interface function with data and auto display."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        
        sample_data = pd.DataFrame({'a': [1, 2, 3]})
        
        result = create_interface(data=sample_data, auto_display=True)
        
        mock_controller_class.assert_called_once_with(auto_display=True)
        mock_controller.load_data.assert_called_once_with(sample_data)
        mock_controller.display.assert_called_once()
        assert result == mock_controller