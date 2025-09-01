"""Core data processing functionality for DataVizTest application.

This module provides the main DataProcessor class responsible for loading,
validating, and processing data from various sources.
"""

from __future__ import annotations

import io
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from pydantic import ValidationError

from ..infrastructure import (
    DataProcessingError,
    DataValidationError,
    get_logger,
    log_performance,
    handle_errors,
)
from ..models import (
    ColumnType,
    DataSource,
    ColumnMetadata,
    DataMetadata,
    ValidationIssue,
    ValidationResult,
    SummaryStats,
    ProcessingOptions,
    DataQualityReport,
)


class DataProcessor:
    """Core data processing class for DataVizTest application."""
    
    def __init__(self):
        """Initialize the data processor."""
        self.logger = get_logger(__name__)
        self._current_data: Optional[pd.DataFrame] = None
        self._metadata: Optional[DataMetadata] = None
    
    @property
    def data(self) -> Optional[pd.DataFrame]:
        """Get the current data."""
        return self._current_data
    
    @property
    def metadata(self) -> Optional[DataMetadata]:
        """Get the current data metadata."""
        return self._metadata
    
    @log_performance
    @handle_errors("data loading")
    def load_data(
        self, 
        source: Union[str, pd.DataFrame, io.StringIO, DataSource],
        **kwargs
    ) -> pd.DataFrame:
        """Load data from various sources.
        
        Args:
            source: Data source (file path, DataFrame, StringIO, or DataSource object)
            **kwargs: Additional arguments for pandas read functions
            
        Returns:
            Loaded DataFrame
            
        Raises:
            DataProcessingError: If data loading fails
        """
        self.logger.info(f"Loading data from source: {type(source)}")
        
        try:
            if isinstance(source, pd.DataFrame):
                df = source.copy()
                data_source = DataSource(
                    source_type="dataframe",
                    name="User DataFrame",
                    description="DataFrame provided by user"
                )
            elif isinstance(source, str):
                df = self._load_from_file(source, **kwargs)
                data_source = DataSource(
                    source_type="file",
                    path=source,
                    name=Path(source).name,
                    description=f"Data loaded from {source}"
                )
            elif isinstance(source, io.StringIO):
                df = pd.read_csv(source, **kwargs)
                data_source = DataSource(
                    source_type="stringio",
                    name="String IO",
                    description="Data from string buffer"
                )
            elif isinstance(source, DataSource):
                if source.path:
                    df = self._load_from_file(source.path, **kwargs)
                else:
                    raise DataProcessingError("DataSource must have a valid path")
                data_source = source
            else:
                raise DataProcessingError(f"Unsupported source type: {type(source)}")
            
            # Validate loaded data
            if df.empty:
                raise DataProcessingError("Loaded data is empty")
            
            # Store data and generate metadata
            self._current_data = df
            self._metadata = self._generate_metadata(df, data_source)
            
            self.logger.info(f"Successfully loaded data with shape {df.shape}")
            return df
            
        except Exception as e:
            if isinstance(e, DataProcessingError):
                raise
            raise DataProcessingError(f"Failed to load data: {str(e)}") from e
    
    def _load_from_file(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Load data from a file based on its extension.
        
        Args:
            file_path: Path to the file
            **kwargs: Additional arguments for pandas read functions
            
        Returns:
            Loaded DataFrame
        """
        path = Path(file_path)
        
        if not path.exists():
            raise DataProcessingError(f"File not found: {file_path}")
        
        file_extension = path.suffix.lower()
        
        try:
            if file_extension == ".csv":
                return pd.read_csv(file_path, **kwargs)
            elif file_extension in [".xlsx", ".xls"]:
                return pd.read_excel(file_path, **kwargs)
            elif file_extension == ".json":
                return pd.read_json(file_path, **kwargs)
            elif file_extension == ".parquet":
                return pd.read_parquet(file_path, **kwargs)
            elif file_extension == ".pickle":
                return pd.read_pickle(file_path, **kwargs)
            else:
                # Try CSV as default
                self.logger.warning(f"Unknown file extension {file_extension}, trying CSV")
                return pd.read_csv(file_path, **kwargs)
                
        except Exception as e:
            raise DataProcessingError(f"Failed to read {file_extension} file: {str(e)}") from e
    
    @handle_errors("metadata generation")
    def _generate_metadata(self, df: pd.DataFrame, source: DataSource) -> DataMetadata:
        """Generate metadata for a DataFrame.
        
        Args:
            df: DataFrame to analyze
            source: Data source information
            
        Returns:
            Generated metadata
        """
        columns_metadata = []
        
        for column in df.columns:
            col_data = df[column]
            
            # Determine column type
            column_type = self._determine_column_type(col_data)
            
            # Get basic statistics
            unique_count = col_data.nunique()
            null_count = col_data.isnull().sum()
            sample_values = col_data.dropna().unique()[:10].tolist()
            
            # Get min/max values based on type
            min_value, max_value = None, None
            if column_type in [ColumnType.NUMERIC, ColumnType.DATETIME]:
                try:
                    min_value = col_data.min()
                    max_value = col_data.max()
                except Exception:
                    pass
            
            column_metadata = ColumnMetadata(
                name=column,
                data_type=column_type,
                unique_count=unique_count,
                null_count=null_count,
                sample_values=sample_values,
                min_value=min_value,
                max_value=max_value
            )
            columns_metadata.append(column_metadata)
        
        return DataMetadata(
            name=source.name,
            shape=(len(df), len(df.columns)),
            columns=columns_metadata,
            source=source
        )
    
    def _determine_column_type(self, series: pd.Series) -> ColumnType:
        """Determine the type of a pandas Series.
        
        Args:
            series: Pandas Series to analyze
            
        Returns:
            Determined column type
        """
        if pd.api.types.is_numeric_dtype(series):
            return ColumnType.NUMERIC
        elif pd.api.types.is_datetime64_any_dtype(series):
            return ColumnType.DATETIME
        elif pd.api.types.is_bool_dtype(series):
            return ColumnType.BOOLEAN
        elif pd.api.types.is_object_dtype(series):
            # Check if it might be categorical
            unique_ratio = series.nunique() / len(series)
            if unique_ratio < 0.5 and series.nunique() < 50:
                return ColumnType.CATEGORICAL
            else:
                return ColumnType.TEXT
        else:
            return ColumnType.UNKNOWN
    
    @log_performance
    @handle_errors("data validation")
    def validate_data(self, df: Optional[pd.DataFrame] = None) -> ValidationResult:
        """Validate data quality and identify issues.
        
        Args:
            df: DataFrame to validate (uses current data if None)
            
        Returns:
            Validation result with issues and summary
        """
        if df is None:
            df = self._current_data
            
        if df is None:
            raise DataValidationError("No data available for validation")
        
        issues = []
        
        # Check for completely empty columns
        empty_columns = df.columns[df.isnull().all()].tolist()
        for col in empty_columns:
            issues.append(ValidationIssue(
                severity="error",
                message=f"Column '{col}' is completely empty",
                column=col
            ))
        
        # Check for duplicate rows
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            duplicate_indices = df[df.duplicated()].index.tolist()
            issues.append(ValidationIssue(
                severity="warning",
                message=f"Found {duplicate_count} duplicate rows",
                row_indices=duplicate_indices
            ))
        
        # Check for high missing data percentage
        for col in df.columns:
            missing_pct = (df[col].isnull().sum() / len(df)) * 100
            if missing_pct > 90:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"Column '{col}' has {missing_pct:.1f}% missing data",
                    column=col
                ))
            elif missing_pct > 50:
                issues.append(ValidationIssue(
                    severity="warning",
                    message=f"Column '{col}' has {missing_pct:.1f}% missing data",
                    column=col
                ))
        
        # Check for potential data type issues
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check for mixed types
                sample_types = set(type(x).__name__ for x in df[col].dropna().head(100))
                if len(sample_types) > 1:
                    issues.append(ValidationIssue(
                        severity="warning",
                        message=f"Column '{col}' contains mixed data types: {sample_types}",
                        column=col
                    ))
        
        # Summary
        error_count = len([i for i in issues if i.severity == "error"])
        warning_count = len([i for i in issues if i.severity == "warning"])
        
        summary = {
            "total_issues": len(issues),
            "errors": error_count,
            "warnings": warning_count
        }
        
        is_valid = error_count == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            summary=summary
        )
    
    @log_performance
    @handle_errors("data cleaning")
    def clean_data(
        self, 
        df: Optional[pd.DataFrame] = None,
        options: Optional[ProcessingOptions] = None
    ) -> pd.DataFrame:
        """Clean data based on processing options.
        
        Args:
            df: DataFrame to clean (uses current data if None)
            options: Processing options
            
        Returns:
            Cleaned DataFrame
        """
        if df is None:
            df = self._current_data
            
        if df is None:
            raise DataProcessingError("No data available for cleaning")
        
        if options is None:
            options = ProcessingOptions()
        
        cleaned_df = df.copy()
        
        # Handle missing values
        if options.handle_missing == "drop":
            cleaned_df = cleaned_df.dropna()
        elif options.handle_missing == "fill_mean":
            numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
            cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(
                cleaned_df[numeric_cols].mean()
            )
        elif options.handle_missing == "fill_median":
            numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
            cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(
                cleaned_df[numeric_cols].median()
            )
        elif options.handle_missing == "fill_mode":
            for col in cleaned_df.columns:
                mode_value = cleaned_df[col].mode()
                if not mode_value.empty:
                    cleaned_df[col] = cleaned_df[col].fillna(mode_value.iloc[0])
        elif options.handle_missing == "fill_zero":
            cleaned_df = cleaned_df.fillna(0)
        
        # Remove duplicates
        if options.remove_duplicates:
            cleaned_df = cleaned_df.drop_duplicates()
        
        # Normalize text
        if options.normalize_text:
            text_cols = cleaned_df.select_dtypes(include=['object']).columns
            for col in text_cols:
                cleaned_df[col] = cleaned_df[col].astype(str).str.strip().str.lower()
        
        # Infer datetime columns
        if options.infer_datetime:
            for col in cleaned_df.select_dtypes(include=['object']).columns:
                try:
                    cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='ignore')
                except Exception:
                    pass
        
        self.logger.info(f"Data cleaned: {df.shape} -> {cleaned_df.shape}")
        return cleaned_df
    
    @handle_errors("summary statistics generation")
    def get_summary_statistics(self, df: Optional[pd.DataFrame] = None) -> SummaryStats:
        """Generate summary statistics for the data.
        
        Args:
            df: DataFrame to analyze (uses current data if None)
            
        Returns:
            Summary statistics
        """
        if df is None:
            df = self._current_data
            
        if df is None:
            raise DataProcessingError("No data available for summary statistics")
        
        # Calculate memory usage
        memory_usage = df.memory_usage(deep=True).sum() / (1024 * 1024)  # MB
        
        # Calculate missing data percentage
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        missing_percentage = (missing_cells / total_cells) * 100 if total_cells > 0 else 0
        
        # Count column types
        if self._metadata:
            numeric_count = len(self._metadata.numerical_columns)
            categorical_count = len(self._metadata.categorical_columns)
            datetime_count = len(self._metadata.datetime_columns)
            text_count = len(self._metadata.text_columns)
        else:
            # Fallback calculation
            numeric_count = len(df.select_dtypes(include=[np.number]).columns)
            categorical_count = len(df.select_dtypes(include=['category']).columns)
            datetime_count = len(df.select_dtypes(include=['datetime64']).columns)
            text_count = len(df.select_dtypes(include=['object']).columns)
        
        # Count duplicated rows
        duplicated_count = df.duplicated().sum()
        
        return SummaryStats(
            total_rows=len(df),
            total_columns=len(df.columns),
            memory_usage_mb=memory_usage,
            missing_data_percentage=missing_percentage,
            numeric_columns_count=numeric_count,
            categorical_columns_count=categorical_count,
            datetime_columns_count=datetime_count,
            text_columns_count=text_count,
            duplicated_rows_count=duplicated_count
        )
    
    def get_column_types(self) -> Dict[str, ColumnType]:
        """Get column types as a dictionary.
        
        Returns:
            Dictionary mapping column names to types
        """
        if self._metadata is None:
            raise DataProcessingError("No metadata available. Load data first.")
        
        return {col.name: col.data_type for col in self._metadata.columns}
    
    def get_data_quality_report(self, df: Optional[pd.DataFrame] = None) -> DataQualityReport:
        """Generate a comprehensive data quality report.
        
        Args:
            df: DataFrame to analyze (uses current data if None)
            
        Returns:
            Complete data quality report
        """
        if df is None:
            df = self._current_data
            
        if df is None:
            raise DataProcessingError("No data available for quality report")
        
        # Generate components
        validation_result = self.validate_data(df)
        summary_stats = self.get_summary_statistics(df)
        
        # Generate recommendations
        recommendations = []
        
        if validation_result.has_errors:
            recommendations.append("Address data quality errors before analysis")
        
        if summary_stats.missing_data_percentage > 20:
            recommendations.append("Consider handling missing data")
        
        if summary_stats.duplicated_rows_count > 0:
            recommendations.append("Remove duplicate rows")
        
        if summary_stats.memory_usage_mb > 500:
            recommendations.append("Consider chunked processing for large dataset")
        
        return DataQualityReport(
            metadata=self._metadata,
            validation_result=validation_result,
            summary_stats=summary_stats,
            recommendations=recommendations
        )