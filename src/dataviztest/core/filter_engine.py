"""Filter engine for DataVizTest application.

This module provides filtering functionality for pandas DataFrames
using various filter types and operators.
"""

from __future__ import annotations

import re
import time
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd

from ..infrastructure import (
    FilterError,
    InvalidFilterError,
    FilterApplicationError,
    get_logger,
    log_performance,
    handle_errors,
)
from ..models import (
    Filter,
    FilterSet,
    FilterResult,
    FilterConfiguration,
    FilterOperator,
    FilterType,
    NumericFilter,
    CategoricalFilter,
    TextFilter,
    DateTimeFilter,
    BooleanFilter,
)


class FilterEngine:
    """Engine for applying filters to pandas DataFrames."""
    
    def __init__(self, config: Optional[FilterConfiguration] = None):
        """Initialize the filter engine.
        
        Args:
            config: Filter configuration options
        """
        self.logger = get_logger(__name__)
        self.config = config or FilterConfiguration()
        self._filter_sets: Dict[str, FilterSet] = {}
        self._filter_cache: Dict[str, pd.DataFrame] = {}
    
    def add_filter_set(self, filter_set: FilterSet) -> None:
        """Add a filter set to the engine.
        
        Args:
            filter_set: FilterSet to add
        """
        self._filter_sets[filter_set.id] = filter_set
        self.logger.debug(f"Added filter set: {filter_set.name}")
    
    def remove_filter_set(self, filter_set_id: str) -> bool:
        """Remove a filter set from the engine.
        
        Args:
            filter_set_id: ID of filter set to remove
            
        Returns:
            True if removed, False if not found
        """
        if filter_set_id in self._filter_sets:
            del self._filter_sets[filter_set_id]
            # Clear related cache entries
            cache_keys_to_remove = [
                key for key in self._filter_cache.keys() 
                if filter_set_id in key
            ]
            for key in cache_keys_to_remove:
                del self._filter_cache[key]
            self.logger.debug(f"Removed filter set: {filter_set_id}")
            return True
        return False
    
    def get_filter_set(self, filter_set_id: str) -> Optional[FilterSet]:
        """Get a filter set by ID.
        
        Args:
            filter_set_id: Filter set ID
            
        Returns:
            FilterSet or None if not found
        """
        return self._filter_sets.get(filter_set_id)
    
    def list_filter_sets(self) -> List[FilterSet]:
        """Get all filter sets.
        
        Returns:
            List of filter sets
        """
        return list(self._filter_sets.values())
    
    @log_performance
    @handle_errors("filter application")
    def apply_filters(
        self, 
        df: pd.DataFrame, 
        filter_set_ids: Optional[List[str]] = None
    ) -> FilterResult:
        """Apply filters to a DataFrame.
        
        Args:
            df: DataFrame to filter
            filter_set_ids: Specific filter set IDs to apply (all if None)
            
        Returns:
            Filter result with statistics
        """
        start_time = time.time()
        original_row_count = len(df)
        
        if filter_set_ids is None:
            filter_sets_to_apply = [fs for fs in self._filter_sets.values() if fs.enabled]
        else:
            filter_sets_to_apply = [
                self._filter_sets[fs_id] for fs_id in filter_set_ids 
                if fs_id in self._filter_sets and self._filter_sets[fs_id].enabled
            ]
        
        if not filter_sets_to_apply:
            return FilterResult(
                original_row_count=original_row_count,
                filtered_row_count=original_row_count,
                filters_applied=[],
                execution_time_ms=0,
                filter_effectiveness={}
            )
        
        # Check cache
        cache_key = self._generate_cache_key(df, filter_sets_to_apply)
        if self.config.enable_caching and cache_key in self._filter_cache:
            cached_result = self._filter_cache[cache_key]
            execution_time = (time.time() - start_time) * 1000
            return FilterResult(
                original_row_count=original_row_count,
                filtered_row_count=len(cached_result),
                filters_applied=[fs.id for fs in filter_sets_to_apply],
                execution_time_ms=execution_time,
                filter_effectiveness={}
            )
        
        # Apply filters
        filtered_df = df.copy()
        filters_applied = []
        filter_effectiveness = {}
        
        for filter_set in filter_sets_to_apply:
            try:
                pre_filter_count = len(filtered_df)
                filtered_df = self._apply_filter_set(filtered_df, filter_set)
                post_filter_count = len(filtered_df)
                
                filters_applied.append(filter_set.id)
                
                # Calculate effectiveness
                if pre_filter_count > 0:
                    effectiveness = ((pre_filter_count - post_filter_count) / pre_filter_count) * 100
                    filter_effectiveness[filter_set.id] = effectiveness
                
                self.logger.debug(
                    f"Filter set '{filter_set.name}' reduced data from "
                    f"{pre_filter_count} to {post_filter_count} rows"
                )
                
            except Exception as e:
                self.logger.error(f"Failed to apply filter set {filter_set.name}: {e}")
                raise FilterApplicationError(
                    f"Failed to apply filter set '{filter_set.name}': {str(e)}"
                ) from e
        
        # Cache result
        if self.config.enable_caching:
            self._filter_cache[cache_key] = filtered_df
        
        execution_time = (time.time() - start_time) * 1000
        
        return FilterResult(
            original_row_count=original_row_count,
            filtered_row_count=len(filtered_df),
            filters_applied=filters_applied,
            execution_time_ms=execution_time,
            filter_effectiveness=filter_effectiveness
        )
    
    def _apply_filter_set(self, df: pd.DataFrame, filter_set: FilterSet) -> pd.DataFrame:
        """Apply a single filter set to a DataFrame.
        
        Args:
            df: DataFrame to filter
            filter_set: Filter set to apply
            
        Returns:
            Filtered DataFrame
        """
        active_filters = filter_set.get_active_filters()
        
        if not active_filters:
            return df
        
        if filter_set.combination_logic == "AND":
            # Apply filters sequentially (AND logic)
            result_df = df.copy()
            for filter_obj in active_filters:
                result_df = self._apply_single_filter(result_df, filter_obj)
            return result_df
        
        else:  # OR logic
            # Apply filters separately and combine with OR
            if len(active_filters) == 1:
                return self._apply_single_filter(df, active_filters[0])
            
            masks = []
            for filter_obj in active_filters:
                try:
                    mask = self._get_filter_mask(df, filter_obj)
                    masks.append(mask)
                except Exception as e:
                    self.logger.warning(f"Failed to apply filter {filter_obj.id}: {e}")
                    continue
            
            if not masks:
                return df
            
            # Combine masks with OR
            combined_mask = masks[0]
            for mask in masks[1:]:
                combined_mask = combined_mask | mask
            
            return df[combined_mask]
    
    def _apply_single_filter(self, df: pd.DataFrame, filter_obj: Filter) -> pd.DataFrame:
        """Apply a single filter to a DataFrame.
        
        Args:
            df: DataFrame to filter
            filter_obj: Filter to apply
            
        Returns:
            Filtered DataFrame
        """
        if filter_obj.column not in df.columns:
            raise InvalidFilterError(f"Column '{filter_obj.column}' not found in data")
        
        mask = self._get_filter_mask(df, filter_obj)
        return df[mask]
    
    def _get_filter_mask(self, df: pd.DataFrame, filter_obj: Filter) -> pd.Series:
        """Get a boolean mask for a filter.
        
        Args:
            df: DataFrame to filter
            filter_obj: Filter to apply
            
        Returns:
            Boolean mask
        """
        column_data = df[filter_obj.column]
        
        if isinstance(filter_obj, NumericFilter):
            return self._apply_numeric_filter(column_data, filter_obj)
        elif isinstance(filter_obj, CategoricalFilter):
            return self._apply_categorical_filter(column_data, filter_obj)
        elif isinstance(filter_obj, TextFilter):
            return self._apply_text_filter(column_data, filter_obj)
        elif isinstance(filter_obj, DateTimeFilter):
            return self._apply_datetime_filter(column_data, filter_obj)
        elif isinstance(filter_obj, BooleanFilter):
            return self._apply_boolean_filter(column_data, filter_obj)
        else:
            raise InvalidFilterError(f"Unsupported filter type: {type(filter_obj)}")
    
    def _apply_numeric_filter(self, series: pd.Series, filter_obj: NumericFilter) -> pd.Series:
        """Apply numeric filter to a series.
        
        Args:
            series: Data series
            filter_obj: Numeric filter
            
        Returns:
            Boolean mask
        """
        if filter_obj.operator == FilterOperator.EQUALS:
            return series == filter_obj.min_value
        elif filter_obj.operator == FilterOperator.NOT_EQUALS:
            return series != filter_obj.min_value
        elif filter_obj.operator == FilterOperator.GREATER_THAN:
            return series > filter_obj.min_value
        elif filter_obj.operator == FilterOperator.GREATER_EQUAL:
            return series >= filter_obj.min_value
        elif filter_obj.operator == FilterOperator.LESS_THAN:
            return series < filter_obj.max_value
        elif filter_obj.operator == FilterOperator.LESS_EQUAL:
            return series <= filter_obj.max_value
        elif filter_obj.operator == FilterOperator.BETWEEN:
            return (series >= filter_obj.min_value) & (series <= filter_obj.max_value)
        elif filter_obj.operator == FilterOperator.IN:
            return series.isin(filter_obj.values or [])
        elif filter_obj.operator == FilterOperator.NOT_IN:
            return ~series.isin(filter_obj.values or [])
        elif filter_obj.operator == FilterOperator.IS_NULL:
            return series.isnull()
        elif filter_obj.operator == FilterOperator.IS_NOT_NULL:
            return series.notnull()
        else:
            raise InvalidFilterError(f"Invalid numeric operator: {filter_obj.operator}")
    
    def _apply_categorical_filter(self, series: pd.Series, filter_obj: CategoricalFilter) -> pd.Series:
        """Apply categorical filter to a series.
        
        Args:
            series: Data series
            filter_obj: Categorical filter
            
        Returns:
            Boolean mask
        """
        if filter_obj.operator == FilterOperator.EQUALS:
            if filter_obj.selected_values:
                return series == filter_obj.selected_values[0]
            return pd.Series([True] * len(series), index=series.index)
        elif filter_obj.operator == FilterOperator.NOT_EQUALS:
            if filter_obj.selected_values:
                return series != filter_obj.selected_values[0]
            return pd.Series([True] * len(series), index=series.index)
        elif filter_obj.operator == FilterOperator.IN:
            mask = series.isin(filter_obj.selected_values)
            return ~mask if filter_obj.exclude_mode else mask
        elif filter_obj.operator == FilterOperator.NOT_IN:
            mask = series.isin(filter_obj.selected_values)
            return mask if filter_obj.exclude_mode else ~mask
        elif filter_obj.operator == FilterOperator.IS_NULL:
            return series.isnull()
        elif filter_obj.operator == FilterOperator.IS_NOT_NULL:
            return series.notnull()
        else:
            raise InvalidFilterError(f"Invalid categorical operator: {filter_obj.operator}")
    
    def _apply_text_filter(self, series: pd.Series, filter_obj: TextFilter) -> pd.Series:
        """Apply text filter to a series.
        
        Args:
            series: Data series
            filter_obj: Text filter
            
        Returns:
            Boolean mask
        """
        # Convert to string and handle case sensitivity
        str_series = series.astype(str)
        text_value = filter_obj.text_value
        
        if not filter_obj.case_sensitive:
            str_series = str_series.str.lower()
            text_value = text_value.lower()
        
        if filter_obj.operator == FilterOperator.EQUALS:
            return str_series == text_value
        elif filter_obj.operator == FilterOperator.NOT_EQUALS:
            return str_series != text_value
        elif filter_obj.operator == FilterOperator.CONTAINS:
            return str_series.str.contains(text_value, na=False)
        elif filter_obj.operator == FilterOperator.NOT_CONTAINS:
            return ~str_series.str.contains(text_value, na=False)
        elif filter_obj.operator == FilterOperator.STARTS_WITH:
            return str_series.str.startswith(text_value, na=False)
        elif filter_obj.operator == FilterOperator.ENDS_WITH:
            return str_series.str.endswith(text_value, na=False)
        elif filter_obj.operator == FilterOperator.IS_NULL:
            return series.isnull()
        elif filter_obj.operator == FilterOperator.IS_NOT_NULL:
            return series.notnull()
        elif filter_obj.operator == FilterOperator.REGEX:
            try:
                flags = 0 if filter_obj.case_sensitive else re.IGNORECASE
                return str_series.str.contains(text_value, regex=True, flags=flags, na=False)
            except re.error as e:
                raise InvalidFilterError(f"Invalid regex pattern: {e}")
        else:
            raise InvalidFilterError(f"Invalid text operator: {filter_obj.operator}")
    
    def _apply_datetime_filter(self, series: pd.Series, filter_obj: DateTimeFilter) -> pd.Series:
        """Apply datetime filter to a series.
        
        Args:
            series: Data series
            filter_obj: DateTime filter
            
        Returns:
            Boolean mask
        """
        # Ensure series is datetime
        if not pd.api.types.is_datetime64_any_dtype(series):
            try:
                series = pd.to_datetime(series)
            except Exception:
                raise FilterApplicationError(f"Cannot convert column to datetime for filtering")
        
        if filter_obj.operator == FilterOperator.EQUALS:
            if filter_obj.start_date:
                return series.dt.date == filter_obj.start_date.date()
            return pd.Series([True] * len(series), index=series.index)
        elif filter_obj.operator == FilterOperator.NOT_EQUALS:
            if filter_obj.start_date:
                return series.dt.date != filter_obj.start_date.date()
            return pd.Series([True] * len(series), index=series.index)
        elif filter_obj.operator == FilterOperator.GREATER_THAN:
            return series > filter_obj.start_date
        elif filter_obj.operator == FilterOperator.GREATER_EQUAL:
            return series >= filter_obj.start_date
        elif filter_obj.operator == FilterOperator.LESS_THAN:
            return series < filter_obj.end_date
        elif filter_obj.operator == FilterOperator.LESS_EQUAL:
            return series <= filter_obj.end_date
        elif filter_obj.operator == FilterOperator.BETWEEN:
            return (series >= filter_obj.start_date) & (series <= filter_obj.end_date)
        elif filter_obj.operator == FilterOperator.IN:
            if filter_obj.date_values:
                dates = [d.date() for d in filter_obj.date_values]
                return series.dt.date.isin(dates)
            return pd.Series([True] * len(series), index=series.index)
        elif filter_obj.operator == FilterOperator.NOT_IN:
            if filter_obj.date_values:
                dates = [d.date() for d in filter_obj.date_values]
                return ~series.dt.date.isin(dates)
            return pd.Series([True] * len(series), index=series.index)
        elif filter_obj.operator == FilterOperator.IS_NULL:
            return series.isnull()
        elif filter_obj.operator == FilterOperator.IS_NOT_NULL:
            return series.notnull()
        else:
            raise InvalidFilterError(f"Invalid datetime operator: {filter_obj.operator}")
    
    def _apply_boolean_filter(self, series: pd.Series, filter_obj: BooleanFilter) -> pd.Series:
        """Apply boolean filter to a series.
        
        Args:
            series: Data series
            filter_obj: Boolean filter
            
        Returns:
            Boolean mask
        """
        if filter_obj.operator == FilterOperator.EQUALS:
            return series == filter_obj.boolean_value
        elif filter_obj.operator == FilterOperator.NOT_EQUALS:
            return series != filter_obj.boolean_value
        elif filter_obj.operator == FilterOperator.IS_NULL:
            return series.isnull()
        elif filter_obj.operator == FilterOperator.IS_NOT_NULL:
            return series.notnull()
        else:
            raise InvalidFilterError(f"Invalid boolean operator: {filter_obj.operator}")
    
    def _generate_cache_key(self, df: pd.DataFrame, filter_sets: List[FilterSet]) -> str:
        """Generate a cache key for the given data and filters.
        
        Args:
            df: DataFrame
            filter_sets: Filter sets to apply
            
        Returns:
            Cache key string
        """
        # Use DataFrame hash and filter set IDs
        df_hash = hash(tuple(df.dtypes.items()))
        filter_ids = sorted([fs.id for fs in filter_sets])
        return f"{df_hash}_{':'.join(filter_ids)}"
    
    def clear_cache(self) -> None:
        """Clear the filter cache."""
        self._filter_cache.clear()
        self.logger.debug("Filter cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        return {
            "cached_results": len(self._filter_cache),
            "filter_sets": len(self._filter_sets)
        }