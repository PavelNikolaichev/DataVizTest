"""Test fixtures for DataVizTest application.

This module provides reusable test data and fixtures for unit and integration tests.
"""

import pandas as pd
import numpy as np
import pytest
from datetime import datetime, timedelta

from src.dataviztest.models import (
    DataSource,
    PlotConfig,
    PlotType,
    NumericFilter,
    CategoricalFilter,
    FilterOperator,
    FilterType,
    MapConfig,
    MapType,
)


@pytest.fixture
def sample_numeric_data():
    """Create sample numeric data for testing."""
    np.random.seed(42)
    
    data = {
        'x': range(100),
        'y': np.random.randn(100),
        'category': np.random.choice(['A', 'B', 'C'], 100),
        'value': np.random.uniform(0, 100, 100),
        'group': np.random.choice(['Group1', 'Group2'], 100)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_geographic_data():
    """Create sample geographic data for testing."""
    data = {
        'city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'],
        'state': ['NY', 'CA', 'IL', 'TX', 'AZ'],
        'latitude': [40.7128, 34.0522, 41.8781, 29.7604, 33.4484],
        'longitude': [-74.0060, -118.2437, -87.6298, -95.3698, -112.0740],
        'population': [8336817, 3979576, 2693976, 2320268, 1680992],
        'area_km2': [783.8, 1302.1, 606.1, 1651.1, 1342.6]
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_datetime_data():
    """Create sample datetime data for testing."""
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(365)]
    
    data = {
        'date': dates,
        'sales': np.random.uniform(1000, 5000, 365),
        'customers': np.random.randint(50, 200, 365),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 365)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_mixed_data():
    """Create sample data with mixed types including missing values."""
    np.random.seed(42)
    
    data = {
        'id': range(1, 101),
        'name': [f'Item_{i}' for i in range(1, 101)],
        'price': np.random.uniform(10, 100, 100),
        'category': np.random.choice(['Electronics', 'Books', 'Clothing', None], 100),
        'rating': np.random.uniform(1, 5, 100),
        'in_stock': np.random.choice([True, False], 100),
        'description': [f'Description for item {i}' if i % 10 != 0 else None for i in range(1, 101)]
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_data_source():
    """Create sample data source configuration."""
    return DataSource(
        source_type="test",
        name="Test Data",
        description="Sample data for testing",
        metadata={"created_by": "test_fixture"}
    )


@pytest.fixture
def sample_plot_config():
    """Create sample plot configuration."""
    return PlotConfig(
        title="Test Plot",
        plot_type=PlotType.SCATTER,
        x_column="x",
        y_column="y",
        color_column="category"
    )


@pytest.fixture
def sample_numeric_filter():
    """Create sample numeric filter."""
    return NumericFilter(
        name="Test Numeric Filter",
        column="value",
        operator=FilterOperator.BETWEEN,
        min_value=10.0,
        max_value=90.0
    )


@pytest.fixture
def sample_categorical_filter():
    """Create sample categorical filter."""
    return CategoricalFilter(
        name="Test Categorical Filter",
        column="category",
        operator=FilterOperator.IN,
        selected_values=["A", "B"]
    )


@pytest.fixture
def sample_map_config():
    """Create sample map configuration."""
    return MapConfig(
        title="Test Map",
        map_type=MapType.SCATTER_MAP,
        latitude_column="latitude",
        longitude_column="longitude",
        value_column="population"
    )


@pytest.fixture
def empty_dataframe():
    """Create empty DataFrame for testing edge cases."""
    return pd.DataFrame()


@pytest.fixture
def large_dataset():
    """Create large dataset for performance testing."""
    np.random.seed(42)
    size = 10000
    
    data = {
        'id': range(size),
        'value1': np.random.randn(size),
        'value2': np.random.uniform(0, 100, size),
        'category': np.random.choice(['A', 'B', 'C', 'D'], size),
        'date': pd.date_range('2020-01-01', periods=size, freq='H'),
        'flag': np.random.choice([True, False], size)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def invalid_coordinate_data():
    """Create data with invalid coordinates for testing."""
    data = {
        'location': ['Invalid Location', 'Another Bad Location'],
        'latitude': [91.0, -91.0],  # Invalid latitudes
        'longitude': [181.0, -181.0],  # Invalid longitudes
        'value': [10, 20]
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def mock_geocoding_data():
    """Create mock geocoding results for testing."""
    return {
        'New York, NY': (40.7128, -74.0060),
        'Los Angeles, CA': (34.0522, -118.2437),
        'Chicago, IL': (41.8781, -87.6298),
        'Invalid Address': None
    }