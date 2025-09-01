"""Unit tests for DataProcessor class."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from src.dataviztest.core import DataProcessor
from src.dataviztest.models import (
    ColumnType,
    DataSource,
    ProcessingOptions,
    ValidationResult,
)
from src.dataviztest.infrastructure import (
    DataProcessingError,
    DataValidationError,
)


class TestDataProcessor:
    """Test cases for DataProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataProcessor()
    
    def test_init(self):
        """Test DataProcessor initialization."""
        assert self.processor.data is None
        assert self.processor.metadata is None
    
    def test_load_dataframe(self, sample_numeric_data):
        """Test loading data from pandas DataFrame."""
        result = self.processor.load_data(sample_numeric_data)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_numeric_data)
        assert self.processor.data is not None
        assert self.processor.metadata is not None
    
    def test_load_empty_dataframe_fails(self, empty_dataframe):
        """Test that loading empty DataFrame raises error."""
        with pytest.raises(DataProcessingError, match="empty"):
            self.processor.load_data(empty_dataframe)
    
    def test_determine_column_types(self, sample_mixed_data):
        """Test column type determination."""
        self.processor.load_data(sample_mixed_data)
        column_types = self.processor.get_column_types()
        
        assert column_types['id'] == ColumnType.NUMERIC
        assert column_types['name'] == ColumnType.TEXT
        assert column_types['price'] == ColumnType.NUMERIC
        assert column_types['in_stock'] == ColumnType.BOOLEAN
    
    def test_validate_data_clean(self, sample_numeric_data):
        """Test validation of clean data."""
        self.processor.load_data(sample_numeric_data)
        result = self.processor.validate_data()
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_data_with_issues(self, sample_mixed_data):
        """Test validation with data quality issues."""
        # Add some problematic data
        problematic_data = sample_mixed_data.copy()
        problematic_data.loc[0, 'category'] = None
        problematic_data.loc[1, 'category'] = None
        problematic_data.loc[2, 'description'] = None
        
        self.processor.load_data(problematic_data)
        result = self.processor.validate_data()
        
        assert isinstance(result, ValidationResult)
        assert len(result.issues) > 0
    
    def test_validate_data_without_loaded_data(self):
        """Test validation without loaded data raises error."""
        with pytest.raises(DataValidationError):
            self.processor.validate_data()
    
    def test_clean_data_drop_missing(self, sample_mixed_data):
        """Test data cleaning with drop missing values."""
        self.processor.load_data(sample_mixed_data)
        
        options = ProcessingOptions(handle_missing="drop")
        cleaned = self.processor.clean_data(options=options)
        
        assert len(cleaned) <= len(sample_mixed_data)
        assert cleaned.isnull().sum().sum() == 0
    
    def test_clean_data_fill_mean(self, sample_numeric_data):
        """Test data cleaning with mean fill."""
        # Add some missing values
        data_with_missing = sample_numeric_data.copy()
        data_with_missing.loc[0:4, 'y'] = np.nan
        
        self.processor.load_data(data_with_missing)
        
        options = ProcessingOptions(handle_missing="fill_mean")
        cleaned = self.processor.clean_data(options=options)
        
        assert cleaned['y'].isnull().sum() == 0
    
    def test_clean_data_remove_duplicates(self, sample_numeric_data):
        """Test removing duplicate rows."""
        # Add duplicate rows
        data_with_duplicates = pd.concat([sample_numeric_data, sample_numeric_data.head(5)])
        
        self.processor.load_data(data_with_duplicates)
        
        options = ProcessingOptions(remove_duplicates=True)
        cleaned = self.processor.clean_data(options=options)
        
        assert len(cleaned) == len(sample_numeric_data)
    
    def test_clean_data_without_loaded_data(self):
        """Test cleaning without loaded data raises error."""
        with pytest.raises(DataProcessingError):
            self.processor.clean_data()
    
    def test_get_summary_statistics(self, sample_numeric_data):
        """Test summary statistics generation."""
        self.processor.load_data(sample_numeric_data)
        stats = self.processor.get_summary_statistics()
        
        assert stats.total_rows == len(sample_numeric_data)
        assert stats.total_columns == len(sample_numeric_data.columns)
        assert stats.memory_usage_mb > 0
        assert stats.numeric_columns_count > 0
    
    def test_get_summary_statistics_without_data(self):
        """Test summary statistics without data raises error."""
        with pytest.raises(DataProcessingError):
            self.processor.get_summary_statistics()
    
    def test_get_column_types_without_metadata(self):
        """Test getting column types without metadata raises error."""
        with pytest.raises(DataProcessingError):
            self.processor.get_column_types()
    
    def test_data_quality_report(self, sample_numeric_data):
        """Test comprehensive data quality report generation."""
        self.processor.load_data(sample_numeric_data)
        report = self.processor.get_data_quality_report()
        
        assert report.metadata is not None
        assert report.validation_result is not None
        assert report.summary_stats is not None
        assert isinstance(report.recommendations, list)
    
    def test_load_from_invalid_source_type(self):
        """Test loading from invalid source type."""
        with pytest.raises(DataProcessingError):
            self.processor.load_data({"invalid": "source"})
    
    @patch('src.dataviztest.core.data_processor.pd.read_csv')
    def test_load_from_file_csv(self, mock_read_csv, sample_numeric_data):
        """Test loading from CSV file."""
        mock_read_csv.return_value = sample_numeric_data
        
        result = self.processor.load_data("test.csv")
        
        mock_read_csv.assert_called_once_with("test.csv")
        assert isinstance(result, pd.DataFrame)
    
    @patch('src.dataviztest.core.data_processor.pd.read_excel')
    def test_load_from_file_excel(self, mock_read_excel, sample_numeric_data):
        """Test loading from Excel file."""
        mock_read_excel.return_value = sample_numeric_data
        
        result = self.processor.load_data("test.xlsx")
        
        mock_read_excel.assert_called_once_with("test.xlsx")
        assert isinstance(result, pd.DataFrame)
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file."""
        with pytest.raises(DataProcessingError, match="File not found"):
            self.processor.load_data("nonexistent_file.csv")
    
    def test_metadata_generation(self, sample_mixed_data):
        """Test metadata generation for mixed data types."""
        self.processor.load_data(sample_mixed_data)
        metadata = self.processor.metadata
        
        assert metadata is not None
        assert len(metadata.columns) == len(sample_mixed_data.columns)
        assert len(metadata.numerical_columns) > 0
        assert len(metadata.categorical_columns) > 0
    
    def test_column_type_determination_edge_cases(self):
        """Test column type determination for edge cases."""
        # Test data with various edge cases
        edge_case_data = pd.DataFrame({
            'all_null': [None, None, None],
            'mixed_numeric_text': [1, 2, 'text'],
            'dates_as_strings': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'bool_as_strings': ['True', 'False', 'True'],
            'high_cardinality': [f'item_{i}' for i in range(100)],
            'low_cardinality': ['A'] * 50 + ['B'] * 50
        })
        
        self.processor.load_data(edge_case_data)
        column_types = self.processor.get_column_types()
        
        # Verify appropriate type detection
        assert column_types['all_null'] in [ColumnType.UNKNOWN, ColumnType.TEXT]
        assert column_types['mixed_numeric_text'] == ColumnType.TEXT
        assert column_types['high_cardinality'] == ColumnType.TEXT
        assert column_types['low_cardinality'] == ColumnType.CATEGORICAL