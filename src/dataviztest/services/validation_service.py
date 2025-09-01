"""Validation service for DataVizTest application.

This module provides comprehensive validation for data, configurations,
and user inputs across the application.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from ..infrastructure import (
    get_logger,
    handle_errors,
)
from ..models import (
    PlotConfig,
    PlotType,
    MapConfig,
    MapType,
    FilterSet,
    Filter,
    ValidationIssue,
    ValidationResult,
)


class ValidationService:
    """Service for validating data and configurations."""
    
    def __init__(self):
        """Initialize the validation service."""
        self.logger = get_logger(__name__)
    
    @handle_errors("dataframe validation")
    def validate_dataframe(
        self, 
        df: pd.DataFrame,
        min_rows: int = 1,
        min_columns: int = 1,
        max_size_mb: float = 1000.0
    ) -> ValidationResult:
        """Validate a pandas DataFrame.
        
        Args:
            df: DataFrame to validate
            min_rows: Minimum required rows
            min_columns: Minimum required columns
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            Validation result
        """
        issues = []
        
        # Check basic requirements
        if df.empty:
            issues.append(ValidationIssue(
                severity="error",
                message="DataFrame is empty",
                details={"shape": df.shape}
            ))
        
        if len(df) < min_rows:
            issues.append(ValidationIssue(
                severity="error",
                message=f"DataFrame has fewer than {min_rows} rows",
                details={"actual_rows": len(df), "minimum_required": min_rows}
            ))
        
        if len(df.columns) < min_columns:
            issues.append(ValidationIssue(
                severity="error",
                message=f"DataFrame has fewer than {min_columns} columns",
                details={"actual_columns": len(df.columns), "minimum_required": min_columns}
            ))
        
        # Check size
        memory_usage = df.memory_usage(deep=True).sum() / (1024 * 1024)  # MB
        if memory_usage > max_size_mb:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"DataFrame size ({memory_usage:.1f}MB) exceeds recommended limit",
                details={"size_mb": memory_usage, "limit_mb": max_size_mb}
            ))
        
        # Check for completely null columns
        null_columns = df.columns[df.isnull().all()].tolist()
        if null_columns:
            issues.append(ValidationIssue(
                severity="error",
                message="Found columns with all null values",
                details={"null_columns": null_columns}
            ))
        
        # Check for duplicate column names
        duplicate_columns = df.columns[df.columns.duplicated()].tolist()
        if duplicate_columns:
            issues.append(ValidationIssue(
                severity="error",
                message="Found duplicate column names",
                details={"duplicate_columns": duplicate_columns}
            ))
        
        # Check for high missing data percentage
        missing_percentage = (df.isnull().sum().sum() / df.size) * 100
        if missing_percentage > 50:
            issues.append(ValidationIssue(
                severity="warning",
                message=f"High percentage of missing data ({missing_percentage:.1f}%)",
                details={"missing_percentage": missing_percentage}
            ))
        
        # Summary
        error_count = len([i for i in issues if i.severity == "error"])
        warning_count = len([i for i in issues if i.severity == "warning"])
        
        summary = {
            "total_issues": len(issues),
            "errors": error_count,
            "warnings": warning_count,
            "memory_usage_mb": memory_usage
        }
        
        is_valid = error_count == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            summary=summary
        )
    
    @handle_errors("plot configuration validation")
    def validate_plot_config(
        self, 
        plot_config: PlotConfig, 
        data: pd.DataFrame
    ) -> bool:
        """Validate a plot configuration against available data.
        
        Args:
            plot_config: Plot configuration to validate
            data: DataFrame to plot
            
        Returns:
            True if configuration is valid
        """
        try:
            # Check if required columns exist
            required_columns = self._get_required_columns_for_plot(plot_config.plot_type)
            
            for req_col in required_columns:
                col_name = getattr(plot_config, req_col, None)
                if col_name and col_name not in data.columns:
                    self.logger.error(f"Required column '{col_name}' not found in data")
                    return False
            
            # Check column types for specific plot types
            if plot_config.plot_type in [PlotType.SCATTER, PlotType.LINE, PlotType.BAR]:
                # X and Y columns should be numeric for most plots
                if plot_config.x_column and plot_config.x_column in data.columns:
                    if plot_config.plot_type != PlotType.BAR:  # Bar plots can have categorical x
                        if not pd.api.types.is_numeric_dtype(data[plot_config.x_column]):
                            # Allow datetime for line plots
                            if not (plot_config.plot_type == PlotType.LINE and 
                                   pd.api.types.is_datetime64_any_dtype(data[plot_config.x_column])):
                                self.logger.warning(f"X column '{plot_config.x_column}' is not numeric")
                
                if plot_config.y_column and plot_config.y_column in data.columns:
                    if not pd.api.types.is_numeric_dtype(data[plot_config.y_column]):
                        self.logger.warning(f"Y column '{plot_config.y_column}' is not numeric")
            
            # Check for histogram specific requirements
            if plot_config.plot_type == PlotType.HISTOGRAM:
                if plot_config.x_column and plot_config.x_column in data.columns:
                    if not pd.api.types.is_numeric_dtype(data[plot_config.x_column]):
                        self.logger.error(f"Histogram requires numeric column, got {data[plot_config.x_column].dtype}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating plot configuration: {e}")
            return False
    
    def _get_required_columns_for_plot(self, plot_type: PlotType) -> List[str]:
        """Get required column attributes for each plot type.
        
        Args:
            plot_type: Type of plot
            
        Returns:
            List of required column attribute names
        """
        requirements = {
            PlotType.SCATTER: ["x_column", "y_column"],
            PlotType.LINE: ["x_column", "y_column"],
            PlotType.BAR: ["x_column", "y_column"],
            PlotType.HISTOGRAM: ["x_column"],
            PlotType.BOX: ["y_column"],
            PlotType.PIE: ["color_column"],
            PlotType.HEATMAP: ["x_column", "y_column"],
            PlotType.BUBBLE: ["x_column", "y_column", "size_column"],
        }
        
        return requirements.get(plot_type, [])
    
    @handle_errors("map configuration validation")
    def validate_map_config(
        self, 
        map_config: MapConfig, 
        data: pd.DataFrame
    ) -> bool:
        """Validate a map configuration against available data.
        
        Args:
            map_config: Map configuration to validate
            data: DataFrame to map
            
        Returns:
            True if configuration is valid
        """
        try:
            # Check for required geographic columns
            if map_config.map_type in [MapType.SCATTER_MAP, MapType.BUBBLE_MAP, MapType.HEATMAP]:
                if not map_config.latitude_column or not map_config.longitude_column:
                    self.logger.error("Latitude and longitude columns required for this map type")
                    return False
                
                # Check if columns exist
                if map_config.latitude_column not in data.columns:
                    self.logger.error(f"Latitude column '{map_config.latitude_column}' not found")
                    return False
                
                if map_config.longitude_column not in data.columns:
                    self.logger.error(f"Longitude column '{map_config.longitude_column}' not found")
                    return False
                
                # Check if coordinates are numeric
                lat_col = data[map_config.latitude_column]
                lon_col = data[map_config.longitude_column]
                
                if not pd.api.types.is_numeric_dtype(lat_col):
                    self.logger.error("Latitude column must be numeric")
                    return False
                
                if not pd.api.types.is_numeric_dtype(lon_col):
                    self.logger.error("Longitude column must be numeric")
                    return False
                
                # Check coordinate ranges
                if lat_col.min() < -90 or lat_col.max() > 90:
                    self.logger.warning("Latitude values outside valid range [-90, 90]")
                
                if lon_col.min() < -180 or lon_col.max() > 180:
                    self.logger.warning("Longitude values outside valid range [-180, 180]")
            
            # Check bubble map specific requirements
            if map_config.map_type == MapType.BUBBLE_MAP:
                if not map_config.size_column:
                    self.logger.error("Size column required for bubble map")
                    return False
                
                if map_config.size_column not in data.columns:
                    self.logger.error(f"Size column '{map_config.size_column}' not found")
                    return False
                
                if not pd.api.types.is_numeric_dtype(data[map_config.size_column]):
                    self.logger.error("Size column must be numeric")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating map configuration: {e}")
            return False
    
    @handle_errors("filter validation")
    def validate_filter(self, filter_obj: Filter, data: pd.DataFrame) -> bool:
        """Validate a filter against available data.
        
        Args:
            filter_obj: Filter to validate
            data: DataFrame to filter
            
        Returns:
            True if filter is valid
        """
        try:
            # Check if column exists
            if filter_obj.column not in data.columns:
                self.logger.error(f"Filter column '{filter_obj.column}' not found in data")
                return False
            
            # Check column data type compatibility
            column_data = data[filter_obj.column]
            
            # For numeric filters, column should be numeric
            if filter_obj.filter_type.value == "numeric":
                if not pd.api.types.is_numeric_dtype(column_data):
                    self.logger.error(f"Numeric filter applied to non-numeric column '{filter_obj.column}'")
                    return False
            
            # For datetime filters, column should be datetime
            if filter_obj.filter_type.value == "datetime":
                if not pd.api.types.is_datetime64_any_dtype(column_data):
                    # Try to convert
                    try:
                        pd.to_datetime(column_data.dropna().head())
                    except:
                        self.logger.error(f"Datetime filter applied to non-datetime column '{filter_obj.column}'")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating filter: {e}")
            return False
    
    @handle_errors("filter set validation")
    def validate_filter_set(self, filter_set: FilterSet, data: pd.DataFrame) -> bool:
        """Validate a filter set against available data.
        
        Args:
            filter_set: Filter set to validate
            data: DataFrame to filter
            
        Returns:
            True if filter set is valid
        """
        try:
            # Validate each filter in the set
            for filter_obj in filter_set.filters:
                if not self.validate_filter(filter_obj, data):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating filter set: {e}")
            return False
    
    def validate_column_selection(
        self, 
        column_name: str, 
        data: pd.DataFrame,
        required_type: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Validate a column selection.
        
        Args:
            column_name: Name of column to validate
            data: DataFrame containing the column
            required_type: Required data type ('numeric', 'categorical', 'datetime')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if column_name not in data.columns:
            return False, f"Column '{column_name}' not found in data"
        
        if required_type:
            column_data = data[column_name]
            
            if required_type == "numeric":
                if not pd.api.types.is_numeric_dtype(column_data):
                    return False, f"Column '{column_name}' is not numeric"
            
            elif required_type == "categorical":
                # Allow both categorical and object types for categorical
                if not (pd.api.types.is_categorical_dtype(column_data) or 
                       pd.api.types.is_object_dtype(column_data)):
                    return False, f"Column '{column_name}' is not categorical"
            
            elif required_type == "datetime":
                if not pd.api.types.is_datetime64_any_dtype(column_data):
                    # Try to convert
                    try:
                        pd.to_datetime(column_data.dropna().head())
                    except:
                        return False, f"Column '{column_name}' cannot be converted to datetime"
        
        return True, ""