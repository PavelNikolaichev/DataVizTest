"""DataVizTest - Modern Data Visualization and Analysis Toolkit.

A comprehensive data visualization and analysis toolkit designed for
interactive data exploration, filtering, and visualization.

This package provides:
- Data processing and validation
- Interactive filtering capabilities  
- Multiple visualization backends
- Geospatial data support
- Jupyter/Colab integration
"""

__version__ = "2.0.0"
__author__ = "DataVizTest Team"
__email__ = "support@dataviztest.com"

# Import core functionality
from .core import (
    DataProcessor,
    FilterEngine,
    VisualizationEngine,
    GeoProcessor,
)

# Import models
from .models import (
    PlotConfig,
    PlotType,
    MapConfig,
    MapType,
    FilterSet,
    NumericFilter,
    CategoricalFilter,
    TextFilter,
    DateTimeFilter,
    BooleanFilter,
    FilterOperator,
    DataSource,
    ProcessingOptions,
)

# Import infrastructure
from .infrastructure import (
    get_settings,
    setup_logging,
    get_logger,
    is_jupyter_environment,
    is_colab_environment,
)

# Main convenience function
def run(data, **kwargs):
    """Initialize DataVizTest with data.
    
    This is the main entry point for the application, similar to the
    original run() function but with improved architecture.
    
    Args:
        data: pandas DataFrame to analyze
        **kwargs: Additional configuration options
        
    Returns:
        Initialized DataVizTest session
    """
    # Set up logging based on environment
    setup_logging()
    
    # Create processor and load data
    processor = DataProcessor()
    processor.load_data(data)
    
    # Create other components
    filter_engine = FilterEngine()
    viz_engine = VisualizationEngine()
    geo_processor = GeoProcessor()
    
    # Return a session object (simplified for now)
    return DataVizTestSession(
        data_processor=processor,
        filter_engine=filter_engine,
        visualization_engine=viz_engine,
        geo_processor=geo_processor
    )


class DataVizTestSession:
    """Main session object for DataVizTest operations."""
    
    def __init__(
        self,
        data_processor: DataProcessor,
        filter_engine: FilterEngine,
        visualization_engine: VisualizationEngine,
        geo_processor: GeoProcessor
    ):
        """Initialize the session.
        
        Args:
            data_processor: Data processing component
            filter_engine: Filtering component
            visualization_engine: Visualization component
            geo_processor: Geospatial processing component
        """
        self.data = data_processor
        self.filters = filter_engine
        self.viz = visualization_engine
        self.geo = geo_processor
        self.logger = get_logger(__name__)
    
    @property
    def current_data(self):
        """Get the current dataset."""
        return self.data.data
    
    @property
    def metadata(self):
        """Get the current data metadata."""
        return self.data.metadata
    
    def create_plot(self, plot_config: PlotConfig):
        """Create a plot with the current data.
        
        Args:
            plot_config: Plot configuration
            
        Returns:
            Plot result
        """
        return self.viz.create_plot(self.current_data, plot_config)
    
    def apply_filters(self, filter_set_ids=None):
        """Apply filters to the current data.
        
        Args:
            filter_set_ids: Specific filter set IDs to apply
            
        Returns:
            Filter result
        """
        return self.filters.apply_filters(self.current_data, filter_set_ids)
    
    def create_map(self, map_config: MapConfig):
        """Create a map with the current data.
        
        Args:
            map_config: Map configuration
            
        Returns:
            Folium map object
        """
        return self.geo.create_map(self.current_data, map_config)
    
    def get_data_summary(self):
        """Get a summary of the current data.
        
        Returns:
            Data quality report
        """
        return self.data.get_data_quality_report()


# Export main components
__all__ = [
    # Main entry point
    "run",
    "DataVizTestSession",
    
    # Core components
    "DataProcessor",
    "FilterEngine", 
    "VisualizationEngine",
    "GeoProcessor",
    
    # Models
    "PlotConfig",
    "PlotType",
    "MapConfig", 
    "MapType",
    "FilterSet",
    "NumericFilter",
    "CategoricalFilter",
    "TextFilter",
    "DateTimeFilter",
    "BooleanFilter",
    "FilterOperator",
    "DataSource",
    "ProcessingOptions",
    
    # Infrastructure
    "get_settings",
    "setup_logging",
    "get_logger",
    "is_jupyter_environment",
    "is_colab_environment",
]