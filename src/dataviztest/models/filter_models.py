"""Filter models for DataVizTest application.

This module defines models for various filter types and operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal

from pydantic import BaseModel, Field, field_validator


class FilterOperator(str, Enum):
    """Filter operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_EQUAL = "greater_equal"
    LESS_THAN = "less_than"
    LESS_EQUAL = "less_equal"
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    REGEX = "regex"


class FilterType(str, Enum):
    """Filter types."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


class BaseFilter(BaseModel):
    """Base filter model."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique filter ID")
    name: str = Field(..., description="Filter display name")
    column: str = Field(..., description="Column to filter on")
    filter_type: FilterType = Field(..., description="Type of filter")
    operator: FilterOperator = Field(..., description="Filter operator")
    enabled: bool = Field(default=True, description="Whether filter is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    class Config:
        use_enum_values = True


class NumericFilter(BaseFilter):
    """Filter for numeric columns."""
    
    filter_type: Literal[FilterType.NUMERIC] = FilterType.NUMERIC
    min_value: Optional[float] = Field(None, description="Minimum value (inclusive)")
    max_value: Optional[float] = Field(None, description="Maximum value (inclusive)")
    values: Optional[List[float]] = Field(None, description="Specific values for IN/NOT_IN operators")
    
    # Operator validation moved to application logic
    
    # Validation moved to application logic for simplicity


class CategoricalFilter(BaseFilter):
    """Filter for categorical columns."""
    
    filter_type: Literal[FilterType.CATEGORICAL] = FilterType.CATEGORICAL
    selected_values: List[str] = Field(default_factory=list, description="Selected category values")
    exclude_mode: bool = Field(default=False, description="Whether to exclude selected values")
    
    # Operator validation moved to application logic


class TextFilter(BaseFilter):
    """Filter for text columns."""
    
    filter_type: Literal[FilterType.TEXT] = FilterType.TEXT
    text_value: str = Field(..., description="Text value to filter by")
    case_sensitive: bool = Field(default=False, description="Whether comparison is case sensitive")
    
    # Operator validation moved to application logic


class DateTimeFilter(BaseFilter):
    """Filter for datetime columns."""
    
    filter_type: Literal[FilterType.DATETIME] = FilterType.DATETIME
    start_date: Optional[datetime] = Field(None, description="Start date (inclusive)")
    end_date: Optional[datetime] = Field(None, description="End date (inclusive)")
    date_values: Optional[List[datetime]] = Field(None, description="Specific dates for IN/NOT_IN")
    
    # Operator validation moved to application logic


class BooleanFilter(BaseFilter):
    """Filter for boolean columns."""
    
    filter_type: Literal[FilterType.BOOLEAN] = FilterType.BOOLEAN
    boolean_value: Optional[bool] = Field(None, description="Boolean value to filter by")
    
    # Operator validation moved to application logic


# Union type for all filter types
Filter = Union[NumericFilter, CategoricalFilter, TextFilter, DateTimeFilter, BooleanFilter]


class FilterSet(BaseModel):
    """A collection of filters with combination logic."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique filter set ID")
    name: str = Field(..., description="Filter set display name")
    filters: List[Filter] = Field(default_factory=list, description="List of filters")
    combination_logic: str = Field(default="AND", description="How to combine filters (AND/OR)")
    enabled: bool = Field(default=True, description="Whether filter set is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    
    # Validation moved to application logic
    
    def add_filter(self, filter_obj: Filter) -> None:
        """Add a filter to the set."""
        self.filters.append(filter_obj)
    
    def remove_filter(self, filter_id: str) -> bool:
        """Remove a filter by ID."""
        initial_length = len(self.filters)
        self.filters = [f for f in self.filters if f.id != filter_id]
        return len(self.filters) < initial_length
    
    def get_active_filters(self) -> List[Filter]:
        """Get all enabled filters."""
        return [f for f in self.filters if f.enabled]


class FilterResult(BaseModel):
    """Result of applying filters to data."""
    
    original_row_count: int = Field(..., description="Number of rows before filtering")
    filtered_row_count: int = Field(..., description="Number of rows after filtering")
    filters_applied: List[str] = Field(..., description="IDs of filters that were applied")
    execution_time_ms: float = Field(..., description="Filter execution time in milliseconds")
    filter_effectiveness: Dict[str, float] = Field(
        default_factory=dict, 
        description="Percentage of rows each filter removed"
    )
    
    @property
    def rows_removed(self) -> int:
        """Number of rows removed by filtering."""
        return self.original_row_count - self.filtered_row_count
    
    @property
    def retention_percentage(self) -> float:
        """Percentage of rows retained after filtering."""
        if self.original_row_count == 0:
            return 100.0
        return (self.filtered_row_count / self.original_row_count) * 100


class FilterConfiguration(BaseModel):
    """Configuration for filter operations."""
    
    enable_caching: bool = Field(default=True, description="Whether to cache filter results")
    parallel_execution: bool = Field(default=False, description="Whether to execute filters in parallel")
    chunk_size: Optional[int] = Field(None, description="Chunk size for large datasets")
    timeout_seconds: int = Field(default=30, description="Timeout for filter operations")
    log_performance: bool = Field(default=True, description="Whether to log performance metrics")