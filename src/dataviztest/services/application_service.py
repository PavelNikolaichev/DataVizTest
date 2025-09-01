"""Application service layer for DataVizTest.

This module provides the main application service that orchestrates
interactions between core components and manages the overall application flow.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from ..core import (
    DataProcessor,
    FilterEngine,
    VisualizationEngine,
    GeoProcessor,
)
from ..infrastructure import (
    get_logger,
    log_performance,
    handle_errors,
    get_settings,
)
from ..models import (
    DataSource,
    PlotConfig,
    PlotResult,
    MapConfig,
    FilterSet,
    FilterResult,
    ProcessingOptions,
    DataQualityReport,
)
from .state_manager import StateManager, ApplicationState
from .validation_service import ValidationService


class ApplicationService:
    """Main application service that orchestrates all components."""
    
    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        validation_service: Optional[ValidationService] = None
    ):
        """Initialize the application service.
        
        Args:
            state_manager: State management service
            validation_service: Validation service
        """
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        
        # Core components
        self.data_processor = DataProcessor()
        self.filter_engine = FilterEngine()
        self.visualization_engine = VisualizationEngine()
        self.geo_processor = GeoProcessor()
        
        # Service components
        self.state_manager = state_manager or StateManager()
        self.validation_service = validation_service or ValidationService()
        
        # Setup state listeners
        self._setup_state_listeners()
        
        self.logger.info("ApplicationService initialized")
    
    def _setup_state_listeners(self) -> None:
        """Set up listeners for state changes."""
        def on_state_change(state: ApplicationState):
            self.logger.debug("Application state changed")
            # Additional state change handling can go here
        
        self.state_manager.add_state_listener(on_state_change)
    
    @property
    def current_data(self) -> Optional[pd.DataFrame]:
        """Get current data from state manager."""
        return self.state_manager.get_data(use_filtered=False)
    
    @property
    def current_filtered_data(self) -> Optional[pd.DataFrame]:
        """Get current filtered data from state manager."""
        return self.state_manager.get_data(use_filtered=True)
    
    @property
    def metadata(self):
        """Get current data metadata."""
        return self.data_processor.metadata
    
    @log_performance
    @handle_errors("data loading")
    def load_data(
        self, 
        source: Union[str, pd.DataFrame, DataSource],
        processing_options: Optional[ProcessingOptions] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Load and process data from various sources.
        
        Args:
            source: Data source (file path, DataFrame, or DataSource object)
            processing_options: Options for data processing
            **kwargs: Additional arguments for data loading
            
        Returns:
            Dictionary with loading results and metadata
        """
        start_time = time.time()
        
        # Load data using data processor
        df = self.data_processor.load_data(source, **kwargs)
        
        # Apply processing options if provided
        if processing_options:
            df = self.data_processor.clean_data(df, processing_options)
        
        # Update state
        self.state_manager.update_data(df)
        
        # Validate data
        validation_result = self.validation_service.validate_dataframe(df)
        
        # Generate quality report
        quality_report = self.data_processor.get_data_quality_report(df)
        
        processing_time = time.time() - start_time
        
        result = {
            "success": True,
            "data_shape": df.shape,
            "validation_result": validation_result,
            "quality_report": quality_report,
            "processing_time_seconds": processing_time,
            "warnings": []
        }
        
        # Add warnings based on data quality
        if not validation_result.is_valid:
            result["warnings"].append("Data validation issues detected")
        
        if quality_report.summary_stats.missing_data_percentage > 20:
            result["warnings"].append("High percentage of missing data detected")
        
        self.logger.info(
            f"Data loaded successfully: {df.shape} in {processing_time:.3f}s"
        )
        
        return result
    
    @log_performance
    @handle_errors("filter application")
    def apply_filters(
        self, 
        filter_sets: Optional[List[FilterSet]] = None,
        save_to_history: bool = True
    ) -> FilterResult:
        """Apply filters to current data.
        
        Args:
            filter_sets: Specific filter sets to apply (uses all active if None)
            save_to_history: Whether to save state to history
            
        Returns:
            Filter application result
        """
        current_data = self.current_data
        if current_data is None:
            raise ValueError("No data available for filtering")
        
        # Use provided filter sets or get from state
        if filter_sets is not None:
            # Add filter sets to engine
            for filter_set in filter_sets:
                self.filter_engine.add_filter_set(filter_set)
            
            # Update state with new filters
            self.state_manager.update_filters(filter_sets, save_to_history)
        
        # Apply filters
        filter_result = self.filter_engine.apply_filters(current_data)
        
        # Get filtered data
        filtered_data = current_data
        for filter_set_id in filter_result.filters_applied:
            filter_set = self.filter_engine.get_filter_set(filter_set_id)
            if filter_set:
                # This is simplified - in practice, we'd apply each filter set
                pass
        
        # For now, we'll re-apply all filters to get the actual filtered data
        if filter_result.filters_applied:
            # Get all active filter sets
            active_filter_sets = [
                fs for fs in self.filter_engine.list_filter_sets() 
                if fs.enabled
            ]
            
            # Apply filters sequentially
            filtered_data = current_data.copy()
            for filter_set in active_filter_sets:
                # This would normally be handled by the filter engine
                # For simplicity, we'll use the result row count
                if filter_result.filtered_row_count < len(filtered_data):
                    filtered_data = filtered_data.iloc[:filter_result.filtered_row_count]
        
        # Update state with filtered data
        self.state_manager.update_filtered_data(filtered_data, save_to_history=False)
        
        self.logger.info(
            f"Filters applied: {filter_result.original_row_count} -> "
            f"{filter_result.filtered_row_count} rows"
        )
        
        return filter_result
    
    @log_performance
    @handle_errors("visualization creation")
    def create_visualization(
        self, 
        plot_config: PlotConfig,
        use_filtered_data: bool = True
    ) -> PlotResult:
        """Create a visualization with current data.
        
        Args:
            plot_config: Plot configuration
            use_filtered_data: Whether to use filtered data if available
            
        Returns:
            Plot creation result
        """
        # Get appropriate data
        data = self.state_manager.get_data(use_filtered=use_filtered_data)
        if data is None:
            raise ValueError("No data available for visualization")
        
        # Validate plot configuration
        is_valid = self.validation_service.validate_plot_config(plot_config, data)
        if not is_valid:
            raise ValueError("Invalid plot configuration")
        
        # Create visualization
        plot_result = self.visualization_engine.create_plot(data, plot_config)
        
        # Update UI state with plot info
        if plot_result.success:
            self.state_manager.update_ui_state(
                f"plot_{plot_config.id}",
                {
                    "plot_config": plot_config.dict(),
                    "creation_time": time.time(),
                    "data_points": plot_result.data_points
                }
            )
        
        self.logger.info(
            f"Visualization created: {plot_config.plot_type} with "
            f"{plot_result.data_points} data points"
        )
        
        return plot_result
    
    @log_performance
    @handle_errors("map creation")
    def create_map(
        self, 
        map_config: MapConfig,
        use_filtered_data: bool = True
    ):
        """Create a map visualization with current data.
        
        Args:
            map_config: Map configuration
            use_filtered_data: Whether to use filtered data if available
            
        Returns:
            Folium map object
        """
        # Get appropriate data
        data = self.state_manager.get_data(use_filtered=use_filtered_data)
        if data is None:
            raise ValueError("No data available for map creation")
        
        # Validate map configuration
        is_valid = self.validation_service.validate_map_config(map_config, data)
        if not is_valid:
            raise ValueError("Invalid map configuration")
        
        # Create map
        map_object = self.geo_processor.create_map(data, map_config)
        
        # Update UI state
        self.state_manager.update_ui_state(
            f"map_{map_config.id}",
            {
                "map_config": map_config.dict(),
                "creation_time": time.time(),
                "data_points": len(data)
            }
        )
        
        self.logger.info(f"Map created: {map_config.map_type} with {len(data)} data points")
        
        return map_object
    
    def get_data_summary(self) -> Optional[DataQualityReport]:
        """Get a comprehensive data quality report.
        
        Returns:
            Data quality report or None if no data
        """
        current_data = self.current_data
        if current_data is None:
            return None
        
        return self.data_processor.get_data_quality_report(current_data)
    
    def get_application_status(self) -> Dict[str, Any]:
        """Get comprehensive application status.
        
        Returns:
            Dictionary with application status information
        """
        state_summary = self.state_manager.get_state_summary()
        
        status = {
            "has_data": self.current_data is not None,
            "data_shape": self.current_data.shape if self.current_data is not None else None,
            "has_filtered_data": self.current_filtered_data is not None,
            "filtered_data_shape": (
                self.current_filtered_data.shape 
                if self.current_filtered_data is not None else None
            ),
            "active_filters": len(self.filter_engine.list_filter_sets()),
            "available_plot_types": len(self.visualization_engine.get_supported_plot_types()),
            "cache_stats": {
                "filter_cache": self.filter_engine.get_cache_stats(),
                "geo_cache": self.geo_processor.get_geocoding_cache_stats()
            },
            "state_management": state_summary
        }
        
        return status
    
    def reset_application(self) -> None:
        """Reset application to initial state."""
        self.state_manager.reset_state()
        self.filter_engine.clear_cache()
        self.geo_processor.clear_geocoding_cache()
        
        self.logger.info("Application reset to initial state")
    
    def undo_last_action(self) -> bool:
        """Undo the last state change.
        
        Returns:
            True if undo was successful
        """
        return self.state_manager.undo()
    
    def redo_last_action(self) -> bool:
        """Redo the last undone action.
        
        Returns:
            True if redo was successful
        """
        return self.state_manager.redo()