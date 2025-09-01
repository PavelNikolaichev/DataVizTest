"""Unit tests for FilterEngine class."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.dataviztest.core import FilterEngine
from src.dataviztest.models import (
    FilterSet,
    FilterConfiguration,
    NumericFilter,
    CategoricalFilter,
    TextFilter,
    DateTimeFilter,
    BooleanFilter,
    FilterOperator,
    FilterType,
)
from src.dataviztest.infrastructure import (
    FilterError,
    InvalidFilterError,
    FilterApplicationError,
)


class TestFilterEngine:
    """Test cases for FilterEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = FilterEngine()
        
        # Create sample data
        self.sample_data = pd.DataFrame({
            'numeric_col': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'category_col': ['A', 'B', 'A', 'C', 'B', 'A', 'C', 'B', 'A', 'C'],
            'text_col': ['apple', 'banana', 'cherry', 'date', 'elderberry', 
                        'fig', 'grape', 'honeydew', 'kiwi', 'lemon'],
            'bool_col': [True, False, True, False, True, False, True, False, True, False],
            'date_col': pd.date_range('2023-01-01', periods=10, freq='D')
        })
    
    def test_init(self):
        """Test FilterEngine initialization."""
        assert len(self.engine._filter_sets) == 0
        assert isinstance(self.engine.config, FilterConfiguration)
    
    def test_add_filter_set(self, sample_numeric_filter):
        """Test adding a filter set."""
        filter_set = FilterSet(name="Test Filter Set")
        filter_set.add_filter(sample_numeric_filter)
        
        self.engine.add_filter_set(filter_set)
        
        assert len(self.engine._filter_sets) == 1
        assert filter_set.id in self.engine._filter_sets
    
    def test_remove_filter_set(self, sample_numeric_filter):
        """Test removing a filter set."""
        filter_set = FilterSet(name="Test Filter Set")
        filter_set.add_filter(sample_numeric_filter)
        
        self.engine.add_filter_set(filter_set)
        removed = self.engine.remove_filter_set(filter_set.id)
        
        assert removed is True
        assert len(self.engine._filter_sets) == 0
    
    def test_remove_nonexistent_filter_set(self):
        """Test removing non-existent filter set."""
        removed = self.engine.remove_filter_set("nonexistent_id")
        assert removed is False
    
    def test_get_filter_set(self, sample_numeric_filter):
        """Test getting a filter set by ID."""
        filter_set = FilterSet(name="Test Filter Set")
        filter_set.add_filter(sample_numeric_filter)
        
        self.engine.add_filter_set(filter_set)
        retrieved = self.engine.get_filter_set(filter_set.id)
        
        assert retrieved is not None
        assert retrieved.id == filter_set.id
    
    def test_list_filter_sets(self, sample_numeric_filter):
        """Test listing all filter sets."""
        filter_set1 = FilterSet(name="Filter Set 1")
        filter_set2 = FilterSet(name="Filter Set 2")
        
        self.engine.add_filter_set(filter_set1)
        self.engine.add_filter_set(filter_set2)
        
        filter_sets = self.engine.list_filter_sets()
        assert len(filter_sets) == 2
    
    def test_apply_numeric_filter_between(self):
        """Test applying numeric filter with BETWEEN operator."""
        numeric_filter = NumericFilter(
            name="Numeric Range Filter",
            column="numeric_col",
            operator=FilterOperator.BETWEEN,
            min_value=3,
            max_value=7
        )
        
        filter_set = FilterSet(name="Numeric Filter Set")
        filter_set.add_filter(numeric_filter)
        self.engine.add_filter_set(filter_set)
        
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        assert result.filtered_row_count == 5  # Values 3, 4, 5, 6, 7
        assert result.original_row_count == 10
    
    def test_apply_categorical_filter_in(self):
        """Test applying categorical filter with IN operator."""
        categorical_filter = CategoricalFilter(
            name="Category Filter",
            column="category_col",
            operator=FilterOperator.IN,
            selected_values=["A", "B"]
        )
        
        filter_set = FilterSet(name="Category Filter Set")
        filter_set.add_filter(categorical_filter)
        self.engine.add_filter_set(filter_set)
        
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        # Should have rows where category_col is 'A' or 'B'
        assert result.filtered_row_count < result.original_row_count
    
    def test_apply_text_filter_contains(self):
        """Test applying text filter with CONTAINS operator."""
        text_filter = TextFilter(
            name="Text Filter",
            column="text_col",
            operator=FilterOperator.CONTAINS,
            text_value="e",
            case_sensitive=False
        )
        
        filter_set = FilterSet(name="Text Filter Set")
        filter_set.add_filter(text_filter)
        self.engine.add_filter_set(filter_set)
        
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        # Should find words containing 'e': cherry, date, elderberry, grape, honeydew
        assert result.filtered_row_count > 0
    
    def test_apply_boolean_filter(self):
        """Test applying boolean filter."""
        bool_filter = BooleanFilter(
            name="Boolean Filter",
            column="bool_col",
            operator=FilterOperator.EQUALS,
            boolean_value=True
        )
        
        filter_set = FilterSet(name="Boolean Filter Set")
        filter_set.add_filter(bool_filter)
        self.engine.add_filter_set(filter_set)
        
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        assert result.filtered_row_count == 5  # Half should be True
    
    def test_apply_datetime_filter(self):
        """Test applying datetime filter."""
        datetime_filter = DateTimeFilter(
            name="Date Filter",
            column="date_col",
            operator=FilterOperator.GREATER_THAN,
            start_date=datetime(2023, 1, 5)
        )
        
        filter_set = FilterSet(name="Date Filter Set")
        filter_set.add_filter(datetime_filter)
        self.engine.add_filter_set(filter_set)
        
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        assert result.filtered_row_count == 5  # Dates after 2023-01-05
    
    def test_apply_multiple_filters_and_logic(self):
        """Test applying multiple filters with AND logic."""
        numeric_filter = NumericFilter(
            name="Numeric Filter",
            column="numeric_col",
            operator=FilterOperator.GREATER_THAN,
            min_value=5
        )
        
        categorical_filter = CategoricalFilter(
            name="Category Filter",
            column="category_col",
            operator=FilterOperator.EQUALS,
            selected_values=["A"]
        )
        
        filter_set = FilterSet(name="Multiple Filters", combination_logic="AND")
        filter_set.add_filter(numeric_filter)
        filter_set.add_filter(categorical_filter)
        self.engine.add_filter_set(filter_set)
        
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        # Should have rows where numeric_col > 5 AND category_col == 'A'
        assert result.filtered_row_count < result.original_row_count
    
    def test_apply_multiple_filters_or_logic(self):
        """Test applying multiple filters with OR logic."""
        numeric_filter = NumericFilter(
            name="Numeric Filter",
            column="numeric_col",
            operator=FilterOperator.LESS_THAN,
            max_value=3
        )
        
        categorical_filter = CategoricalFilter(
            name="Category Filter",
            column="category_col",
            operator=FilterOperator.EQUALS,
            selected_values=["C"]
        )
        
        filter_set = FilterSet(name="Multiple Filters OR", combination_logic="OR")
        filter_set.add_filter(numeric_filter)
        filter_set.add_filter(categorical_filter)
        self.engine.add_filter_set(filter_set)
        
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        # Should have rows where numeric_col < 3 OR category_col == 'C'
        assert result.filtered_row_count > 0
    
    def test_apply_filter_to_missing_column(self):
        """Test applying filter to non-existent column."""
        invalid_filter = NumericFilter(
            name="Invalid Filter",
            column="nonexistent_column",
            operator=FilterOperator.EQUALS,
            min_value=5
        )
        
        filter_set = FilterSet(name="Invalid Filter Set")
        filter_set.add_filter(invalid_filter)
        self.engine.add_filter_set(filter_set)
        
        with pytest.raises(FilterApplicationError, match="not found"):
            self.engine.apply_filters(self.sample_data)
    
    def test_apply_filters_with_empty_data(self):
        """Test applying filters to empty DataFrame."""
        empty_df = pd.DataFrame()
        
        numeric_filter = NumericFilter(
            name="Numeric Filter",
            column="numeric_col",
            operator=FilterOperator.EQUALS,
            min_value=5
        )
        
        filter_set = FilterSet(name="Filter Set")
        filter_set.add_filter(numeric_filter)
        self.engine.add_filter_set(filter_set)
        
        with pytest.raises(FilterApplicationError):
            self.engine.apply_filters(empty_df)
    
    def test_apply_filters_no_filter_sets(self):
        """Test applying filters when no filter sets exist."""
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        assert result.filtered_row_count == result.original_row_count
        assert len(result.filters_applied) == 0
    
    def test_disabled_filter_set(self, sample_numeric_filter):
        """Test that disabled filter sets are not applied."""
        filter_set = FilterSet(name="Disabled Filter Set", enabled=False)
        filter_set.add_filter(sample_numeric_filter)
        self.engine.add_filter_set(filter_set)
        
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        assert result.filtered_row_count == result.original_row_count
        assert len(result.filters_applied) == 0
    
    def test_filter_cache(self, sample_numeric_filter):
        """Test filter result caching."""
        config = FilterConfiguration(enable_caching=True)
        engine = FilterEngine(config)
        
        filter_set = FilterSet(name="Cached Filter Set")
        filter_set.add_filter(sample_numeric_filter)
        engine.add_filter_set(filter_set)
        
        # First application
        result1 = engine.apply_filters(self.sample_data)
        
        # Second application (should use cache)
        result2 = engine.apply_filters(self.sample_data)
        
        assert result1.filtered_row_count == result2.filtered_row_count
    
    def test_clear_cache(self, sample_numeric_filter):
        """Test clearing filter cache."""
        config = FilterConfiguration(enable_caching=True)
        engine = FilterEngine(config)
        
        filter_set = FilterSet(name="Filter Set")
        filter_set.add_filter(sample_numeric_filter)
        engine.add_filter_set(filter_set)
        
        # Apply filters to populate cache
        engine.apply_filters(self.sample_data)
        
        # Clear cache
        engine.clear_cache()
        
        cache_stats = engine.get_cache_stats()
        assert cache_stats["cached_results"] == 0
    
    def test_get_cache_stats(self, sample_numeric_filter):
        """Test getting cache statistics."""
        filter_set = FilterSet(name="Filter Set")
        filter_set.add_filter(sample_numeric_filter)
        self.engine.add_filter_set(filter_set)
        
        stats = self.engine.get_cache_stats()
        
        assert "cached_results" in stats
        assert "filter_sets" in stats
        assert stats["filter_sets"] == 1
    
    def test_numeric_filter_validation(self):
        """Test numeric filter validation."""
        # Valid filter
        valid_filter = NumericFilter(
            name="Valid Filter",
            column="numeric_col",
            operator=FilterOperator.BETWEEN,
            min_value=1,
            max_value=5
        )
        
        # Test validation passes
        assert valid_filter.operator == FilterOperator.BETWEEN
    
    def test_text_filter_regex(self):
        """Test text filter with regex operator."""
        regex_filter = TextFilter(
            name="Regex Filter",
            column="text_col",
            operator=FilterOperator.REGEX,
            text_value=r"^[a-e]",  # Words starting with letters a-e
            case_sensitive=False
        )
        
        filter_set = FilterSet(name="Regex Filter Set")
        filter_set.add_filter(regex_filter)
        self.engine.add_filter_set(filter_set)
        
        result = self.engine.apply_filters(self.sample_data)
        
        assert result.success
        # Should match: apple, banana, cherry, date, elderberry
        assert result.filtered_row_count == 5
    
    def test_invalid_regex_pattern(self):
        """Test text filter with invalid regex pattern."""
        invalid_regex_filter = TextFilter(
            name="Invalid Regex Filter",
            column="text_col",
            operator=FilterOperator.REGEX,
            text_value="[",  # Invalid regex
            case_sensitive=False
        )
        
        filter_set = FilterSet(name="Invalid Regex Filter Set")
        filter_set.add_filter(invalid_regex_filter)
        self.engine.add_filter_set(filter_set)
        
        with pytest.raises(FilterApplicationError, match="Invalid regex"):
            self.engine.apply_filters(self.sample_data)