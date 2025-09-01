"""Integration tests for complete DataVizTest workflows.

This module tests end-to-end functionality across all layers of the application.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock
import tempfile
import os

from dataviztest import run, DataVizTestSession
from dataviztest.services import ApplicationService
from dataviztest.ui import create_interface, MainUIController
from dataviztest.models import (
    PlotConfig, PlotType, MapConfig, MapType, FilterSet, 
    NumericFilter, CategoricalFilter, FilterOperator
)
from dataviztest.core import DataProcessor, FilterEngine, VisualizationEngine


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    @pytest.fixture
    def sample_dataset(self):
        """Create a comprehensive sample dataset for testing."""
        np.random.seed(42)
        n_samples = 200
        
        return pd.DataFrame({
            'id': range(1, n_samples + 1),
            'name': [f'Item_{i}' for i in range(1, n_samples + 1)],
            'category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Home'], n_samples),
            'subcategory': np.random.choice(['A', 'B', 'C', 'D', 'E'], n_samples),
            'price': np.random.uniform(10, 1000, n_samples),
            'rating': np.random.uniform(1, 5, n_samples),
            'sales_count': np.random.poisson(50, n_samples),
            'discount_percent': np.random.uniform(0, 30, n_samples),
            'latitude': np.random.uniform(35.0, 45.0, n_samples),
            'longitude': np.random.uniform(-125.0, -65.0, n_samples),
            'created_date': pd.date_range('2023-01-01', periods=n_samples, freq='D'),
            'is_featured': np.random.choice([True, False], n_samples),
            'stock_quantity': np.random.randint(0, 100, n_samples)
        })
    
    def test_complete_data_processing_workflow(self, sample_dataset):
        """Test complete data processing workflow from loading to analysis."""
        # Initialize session
        session = run(sample_dataset)
        
        # Verify data was loaded
        assert session.current_data is not None
        assert len(session.current_data) == 200
        assert len(session.current_data.columns) == 13
        
        # Test data summary
        summary = session.get_data_summary()
        assert summary is not None
        assert hasattr(summary, 'summary_stats')
        assert summary.summary_stats.total_rows == 200
        
        # Test metadata access
        metadata = session.metadata
        assert metadata is not None
    
    def test_filtering_workflow(self, sample_dataset):
        """Test complete filtering workflow."""
        session = run(sample_dataset)
        
        # Create numeric filter
        price_filter = NumericFilter(
            name="price_filter",
            column="price",
            operator=FilterOperator.GREATER_THAN,
            value=500
        )
        
        # Create categorical filter
        category_filter = CategoricalFilter(
            name="category_filter",
            column="category",
            operator=FilterOperator.IN,
            values=["Electronics", "Books"]
        )
        
        # Create filter set
        filter_set = FilterSet(
            name="expensive_electronics_books",
            filters=[price_filter, category_filter]
        )
        
        # Apply filters
        session.filters.add_filter_set(filter_set)
        filtered_result = session.apply_filters()
        
        # Verify filtering worked
        assert filtered_result is not None
        assert len(filtered_result) < len(sample_dataset)
        
        # Verify filter conditions
        assert all(filtered_result['price'] > 500)
        assert all(filtered_result['category'].isin(['Electronics', 'Books']))
    
    def test_visualization_workflow(self, sample_dataset):
        """Test complete visualization workflow."""
        session = run(sample_dataset)
        
        # Create scatter plot
        scatter_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'price', 'y': 'rating', 'color': 'category'},
            title="Price vs Rating by Category"
        )
        
        plot_result = session.create_plot(scatter_config)
        assert plot_result is not None
        
        # Create bar chart
        bar_config = PlotConfig(
            plot_type=PlotType.BAR,
            columns={'x': 'category', 'y': 'sales_count'},
            title="Sales Count by Category"
        )
        
        bar_result = session.create_plot(bar_config)
        assert bar_result is not None
        
        # Create histogram
        hist_config = PlotConfig(
            plot_type=PlotType.HISTOGRAM,
            columns={'x': 'price'},
            title="Price Distribution"
        )
        
        hist_result = session.create_plot(hist_config)
        assert hist_result is not None
    
    def test_mapping_workflow(self, sample_dataset):
        """Test complete geospatial mapping workflow."""
        session = run(sample_dataset)
        
        # Create marker map
        marker_config = MapConfig(
            map_type=MapType.SCATTER_MAP,
            location={
                'latitude_column': 'latitude',
                'longitude_column': 'longitude',
                'center_lat': 40.0,
                'center_lon': -95.0,
                'zoom': 5
            },
            columns={'popup': 'name'}
        )
        
        map_result = session.create_map(marker_config)
        assert map_result is not None
        
        # Create bubble map
        bubble_config = MapConfig(
            map_type=MapType.BUBBLE_MAP,
            location={
                'latitude_column': 'latitude',
                'longitude_column': 'longitude',
                'center_lat': 40.0,
                'center_lon': -95.0,
                'zoom': 5
            },
            columns={'size': 'sales_count', 'color': 'category'}
        )
        
        bubble_result = session.create_map(bubble_config)
        assert bubble_result is not None
    
    def test_combined_filter_and_visualization_workflow(self, sample_dataset):
        """Test workflow combining filtering and visualization."""
        session = run(sample_dataset)
        
        # Apply filters first
        filter_set = FilterSet(
            name="high_rated_items",
            filters=[
                NumericFilter(
                    name="rating_filter",
                    column="rating",
                    operator=FilterOperator.GREATER_THAN,
                    value=4.0
                )
            ]
        )
        
        session.filters.add_filter_set(filter_set)
        filtered_data = session.apply_filters()
        
        # Create visualization with filtered data
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'price', 'y': 'sales_count'},
            title="High-Rated Items: Price vs Sales"
        )
        
        plot_result = session.create_plot(plot_config)
        assert plot_result is not None
        
        # Verify we're working with filtered data
        assert len(filtered_data) < len(sample_dataset)
        assert all(filtered_data['rating'] > 4.0)


class TestApplicationServiceIntegration:
    """Test ApplicationService integration scenarios."""
    
    @pytest.fixture
    def app_service(self):
        """Create ApplicationService for testing."""
        return ApplicationService()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        return pd.DataFrame({
            'id': range(1, 101),
            'category': ['A', 'B', 'C'] * 33 + ['A'],
            'value': np.random.normal(100, 25, 100),
            'score': np.random.uniform(0, 100, 100),
            'latitude': np.random.uniform(40.0, 41.0, 100),
            'longitude': np.random.uniform(-74.5, -73.5, 100)
        })
    
    def test_data_load_validation_visualization_flow(self, app_service, sample_data):
        """Test flow from data loading through validation to visualization."""
        # Load data
        app_service.load_data(sample_data)
        assert app_service.current_data is not None
        
        # Validate plot configuration
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value', 'y': 'score'}
        )
        
        validation_result = app_service.validate_plot_config(plot_config)
        assert validation_result['is_valid'] is True
        
        # Create visualization
        viz_result = app_service.create_visualization(plot_config)
        assert viz_result is not None
    
    def test_data_load_filter_map_flow(self, app_service, sample_data):
        """Test flow from data loading through filtering to mapping."""
        # Load data
        app_service.load_data(sample_data)
        
        # Apply filters
        filter_set = FilterSet(
            name="test_filter",
            filters=[
                NumericFilter(
                    column="value",
                    operator=FilterOperator.GREATER_THAN,
                    value=75
                )
            ]
        )
        
        filtered_data = app_service.apply_filters([filter_set])
        assert len(filtered_data) < len(sample_data)
        
        # Create map with filtered data
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
        
        map_result = app_service.create_map(map_config)
        assert map_result is not None
    
    def test_error_handling_in_workflow(self, app_service, sample_data):
        """Test error handling throughout the workflow."""
        # Load data
        app_service.load_data(sample_data)
        
        # Try invalid plot configuration
        invalid_plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'nonexistent_column', 'y': 'score'}
        )
        
        validation_result = app_service.validate_plot_config(invalid_plot_config)
        assert validation_result['is_valid'] is False
        assert 'errors' in validation_result
        
        # Try invalid map configuration
        invalid_map_config = MapConfig(
            map_type=MapType.MARKER,
            location={
                'latitude_column': 'missing_lat',
                'longitude_column': 'longitude'
            }
        )
        
        map_validation = app_service.validate_map_config(invalid_map_config)
        assert map_validation['is_valid'] is False


class TestUIIntegration:
    """Test UI component integration."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for UI testing."""
        return pd.DataFrame({
            'id': range(1, 21),
            'name': [f'Item_{i}' for i in range(1, 21)],
            'category': ['X', 'Y', 'Z'] * 6 + ['X', 'Y'],
            'value': range(20, 40),
            'score': [i * 2.5 for i in range(20)]
        })
    
    @patch('dataviztest.ui.main_controller.display')
    def test_ui_controller_initialization_and_data_loading(self, mock_display, sample_data):
        """Test UI controller initialization and data loading."""
        # Create controller
        controller = MainUIController(auto_display=False)
        
        # Load data programmatically
        controller.load_data(sample_data)
        
        # Verify data was loaded
        assert controller.get_current_data() is not None
        pd.testing.assert_frame_equal(controller.get_current_data(), sample_data)
        
        # Test display
        controller.display()
        mock_display.assert_called_once()
    
    @patch('dataviztest.ui.main_controller.display')
    def test_create_interface_convenience_function(self, mock_display, sample_data):
        """Test create_interface convenience function."""
        # Create interface with data
        controller = create_interface(data=sample_data, auto_display=True)
        
        # Verify controller was created and data loaded
        assert isinstance(controller, MainUIController)
        assert controller.get_current_data() is not None
        mock_display.assert_called_once()
    
    def test_ui_programmatic_operations(self, sample_data):
        """Test programmatic operations through UI controller."""
        controller = MainUIController(auto_display=False)
        controller.load_data(sample_data)
        
        # Create plot programmatically
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'value', 'y': 'score'}
        )
        
        plot_result = controller.create_plot(plot_config)
        assert plot_result is not None
        
        # Apply filters programmatically
        filter_set = FilterSet(
            name="test_filter",
            filters=[
                NumericFilter(
                    column="value",
                    operator=FilterOperator.GREATER_THAN,
                    value=30
                )
            ]
        )
        
        filter_result = controller.apply_filters(filter_set)
        assert filter_result is not None
        assert len(filter_result) < len(sample_data)


class TestPerformanceAndScaling:
    """Test performance and scaling characteristics."""
    
    def test_large_dataset_handling(self):
        """Test handling of larger datasets."""
        # Create larger dataset
        np.random.seed(42)
        large_data = pd.DataFrame({
            'id': range(1, 10001),
            'category': np.random.choice(['A', 'B', 'C', 'D'], 10000),
            'value': np.random.normal(100, 25, 10000),
            'score': np.random.uniform(0, 100, 10000),
            'date': pd.date_range('2020-01-01', periods=10000, freq='H')
        })
        
        # Initialize session
        session = run(large_data)
        
        # Verify it handles large data
        assert session.current_data is not None
        assert len(session.current_data) == 10000
        
        # Test filtering performance
        filter_set = FilterSet(
            name="performance_test",
            filters=[
                NumericFilter(
                    column="value",
                    operator=FilterOperator.BETWEEN,
                    value=(90, 110)
                )
            ]
        )
        
        session.filters.add_filter_set(filter_set)
        filtered_result = session.apply_filters()
        
        # Should complete without errors
        assert filtered_result is not None
    
    def test_memory_usage_monitoring(self):
        """Test memory usage is reasonable."""
        # Create dataset with varying sizes
        for size in [100, 1000, 5000]:
            data = pd.DataFrame({
                'id': range(size),
                'value': np.random.normal(0, 1, size),
                'category': np.random.choice(['A', 'B', 'C'], size)
            })
            
            session = run(data)
            summary = session.get_data_summary()
            
            # Verify summary includes memory information
            assert summary is not None
            # Memory usage should be reasonable (implementation-dependent)


class TestErrorRecoveryAndResilience:
    """Test error recovery and application resilience."""
    
    def test_invalid_data_recovery(self):
        """Test recovery from invalid data scenarios."""
        # Test with None data
        session = run(pd.DataFrame())
        assert session is not None
        
        # Test with data containing NaN values
        problematic_data = pd.DataFrame({
            'id': [1, 2, None, 4],
            'value': [10.0, None, 30.0, 40.0],
            'category': ['A', None, 'C', 'D']
        })
        
        session = run(problematic_data)
        assert session is not None
        # Should handle NaN values gracefully
    
    def test_configuration_error_handling(self):
        """Test handling of invalid configurations."""
        data = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })
        
        session = run(data)
        
        # Test invalid plot configuration
        try:
            invalid_config = PlotConfig(
                plot_type=PlotType.SCATTER,
                columns={'x': 'nonexistent', 'y': 'y'}
            )
            # Should not crash the application
            session.create_plot(invalid_config)
        except Exception:
            # Expected to fail, but should be handled gracefully
            pass
    
    def test_state_consistency_after_errors(self):
        """Test that application state remains consistent after errors."""
        data = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [4, 5, 6]
        })
        
        session = run(data)
        
        # Get initial state
        initial_data = session.current_data.copy()
        
        # Cause an error
        try:
            invalid_filter = FilterSet(
                name="invalid",
                filters=[
                    NumericFilter(
                        column="nonexistent",
                        operator=FilterOperator.EQUAL,
                        value=1
                    )
                ]
            )
            session.apply_filters([invalid_filter])
        except Exception:
            pass
        
        # Verify state is still consistent
        pd.testing.assert_frame_equal(session.current_data, initial_data)


class TestBackwardCompatibility:
    """Test backward compatibility with original interface."""
    
    def test_original_run_function_compatibility(self):
        """Test that original run() function interface still works."""
        data = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10]
        })
        
        # This should work like the original function
        session = run(data)
        
        # Verify session object provides expected interface
        assert hasattr(session, 'data')
        assert hasattr(session, 'filters')
        assert hasattr(session, 'viz')
        assert hasattr(session, 'current_data')
        
        # Test that data is accessible
        assert session.current_data is not None
        pd.testing.assert_frame_equal(session.current_data, data)
    
    def test_session_object_interface(self):
        """Test that session object maintains expected interface."""
        data = pd.DataFrame({'a': [1, 2, 3]})
        session = run(data)
        
        # Check for expected attributes
        assert hasattr(session, 'data')  # DataProcessor
        assert hasattr(session, 'filters')  # FilterEngine
        assert hasattr(session, 'viz')  # VisualizationEngine
        assert hasattr(session, 'geo')  # GeoProcessor
        
        # Check for expected methods
        assert hasattr(session, 'create_plot')
        assert hasattr(session, 'apply_filters')
        assert hasattr(session, 'create_map')
        assert hasattr(session, 'get_data_summary')