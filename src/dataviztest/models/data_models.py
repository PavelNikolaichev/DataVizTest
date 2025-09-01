"""Data models for DataVizTest application.

This module defines Pydantic models for data structures used throughout
the application, providing validation and serialization capabilities.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel, Field, validator


class ColumnType(str, Enum):
    """Column data types."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"


class DataSource(BaseModel):
    """Data source information."""
    
    source_type: str = Field(..., description="Type of data source")
    path: Optional[str] = Field(None, description="File path or URL")
    name: str = Field(..., description="Display name for the data source")
    description: Optional[str] = Field(None, description="Data source description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ColumnMetadata(BaseModel):
    """Metadata for a data column."""
    
    name: str = Field(..., description="Column name")
    data_type: ColumnType = Field(..., description="Column data type")
    nullable: bool = Field(default=True, description="Whether column can contain nulls")
    unique_count: int = Field(..., description="Number of unique values")
    null_count: int = Field(default=0, description="Number of null values")
    sample_values: List[Any] = Field(default_factory=list, description="Sample values")
    min_value: Optional[Union[float, str, datetime]] = Field(None, description="Minimum value")
    max_value: Optional[Union[float, str, datetime]] = Field(None, description="Maximum value")
    description: Optional[str] = Field(None, description="Column description")


class DataMetadata(BaseModel):
    """Metadata for a complete dataset."""
    
    name: str = Field(..., description="Dataset name")
    shape: tuple[int, int] = Field(..., description="Dataset shape (rows, columns)")
    columns: List[ColumnMetadata] = Field(..., description="Column metadata")
    source: Optional[DataSource] = Field(None, description="Data source information")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    @property
    def numerical_columns(self) -> List[str]:
        """Get list of numerical column names."""
        return [col.name for col in self.columns if col.data_type == ColumnType.NUMERIC]
    
    @property
    def categorical_columns(self) -> List[str]:
        """Get list of categorical column names."""
        return [col.name for col in self.columns if col.data_type == ColumnType.CATEGORICAL]
    
    @property
    def datetime_columns(self) -> List[str]:
        """Get list of datetime column names."""
        return [col.name for col in self.columns if col.data_type == ColumnType.DATETIME]
    
    @property
    def text_columns(self) -> List[str]:
        """Get list of text column names."""
        return [col.name for col in self.columns if col.data_type == ColumnType.TEXT]


class ValidationIssue(BaseModel):
    """A data validation issue."""
    
    severity: str = Field(..., description="Issue severity (error, warning, info)")
    message: str = Field(..., description="Issue description")
    column: Optional[str] = Field(None, description="Column involved (if applicable)")
    row_indices: List[int] = Field(default_factory=list, description="Affected row indices")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class ValidationResult(BaseModel):
    """Result of data validation."""
    
    is_valid: bool = Field(..., description="Whether data passed validation")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Validation issues")
    summary: Dict[str, int] = Field(default_factory=dict, description="Issue summary")
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get error-level issues."""
        return [issue for issue in self.issues if issue.severity == "error"]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get warning-level issues."""
        return [issue for issue in self.issues if issue.severity == "warning"]
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


class SummaryStats(BaseModel):
    """Summary statistics for a dataset."""
    
    total_rows: int = Field(..., description="Total number of rows")
    total_columns: int = Field(..., description="Total number of columns")
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    missing_data_percentage: float = Field(..., description="Percentage of missing data")
    numeric_columns_count: int = Field(..., description="Number of numeric columns")
    categorical_columns_count: int = Field(..., description="Number of categorical columns")
    datetime_columns_count: int = Field(..., description="Number of datetime columns")
    text_columns_count: int = Field(..., description="Number of text columns")
    duplicated_rows_count: int = Field(default=0, description="Number of duplicated rows")


class ProcessingOptions(BaseModel):
    """Options for data processing operations."""
    
    handle_missing: str = Field(default="keep", description="How to handle missing values")
    remove_duplicates: bool = Field(default=False, description="Whether to remove duplicate rows")
    normalize_text: bool = Field(default=False, description="Whether to normalize text columns")
    infer_datetime: bool = Field(default=True, description="Whether to infer datetime columns")
    chunk_size: Optional[int] = Field(None, description="Chunk size for processing")
    
    @validator("handle_missing")
    def validate_handle_missing(cls, v):
        """Validate missing value handling option."""
        valid_options = ["keep", "drop", "fill_mean", "fill_median", "fill_mode", "fill_zero"]
        if v not in valid_options:
            raise ValueError(f"handle_missing must be one of {valid_options}")
        return v


# Additional utility models

class DataQualityReport(BaseModel):
    """Comprehensive data quality report."""
    
    metadata: DataMetadata = Field(..., description="Dataset metadata")
    validation_result: ValidationResult = Field(..., description="Validation results")
    summary_stats: SummaryStats = Field(..., description="Summary statistics")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation time")