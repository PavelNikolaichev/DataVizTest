"""Main UI controller for DataVizTest application.

This module provides the main interface controller that orchestrates
all widgets and provides a unified user interface.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
import logging

import ipywidgets as widgets
import pandas as pd

from .widgets import FilterWidget, PlottingWidget, MappingWidget
from .interactive_components import (
    DataColumnSelector,
    ActionButton,
    MessageDisplay
)
from ..infrastructure import get_logger, get_settings, handle_errors
from ..models import PlotConfig, MapConfig, FilterSet
from ..services import ApplicationService, StateManager


class MainUIController:
    """Main UI controller that orchestrates all application widgets."""
    
    def __init__(
        self,
        app_service: Optional[ApplicationService] = None,
        auto_display: bool = True
    ):
        """Initialize the main UI controller.
        
        Args:
            app_service: Application service instance
            auto_display: Whether to automatically display the interface
        """
        self.app_service = app_service or ApplicationService()
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        
        # Main interface components
        self._main_widget: Optional[widgets.Widget] = None
        self._data_panel: Optional[widgets.Widget] = None
        self._filter_widget: Optional[FilterWidget] = None
        self._plotting_widget: Optional[PlottingWidget] = None
        self._mapping_widget: Optional[MappingWidget] = None
        self._message_display: Optional[MessageDisplay] = None
        
        # State
        self._current_data: Optional[pd.DataFrame] = None
        self._initialized = False
        
        if auto_display:
            self._create_interface()
    
    def _create_interface(self) -> None:
        """Create the main user interface."""
        try:
            # Create message display
            self._message_display = MessageDisplay()
            
            # Create data management panel
            self._data_panel = self._create_data_panel()
            
            # Create widget instances
            self._filter_widget = FilterWidget(app_service=self.app_service)
            self._plotting_widget = PlottingWidget(app_service=self.app_service)
            self._mapping_widget = MappingWidget(app_service=self.app_service)
            
            # Create tabbed interface
            self._main_widget = self._create_tabbed_interface()
            
            # Set up interactions
            self._setup_interactions()
            
            self._initialized = True
            self.logger.info("Main UI interface created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create interface: {e}")
            if self._message_display:
                self._message_display.show_message(
                    f"Failed to initialize interface: {str(e)}",
                    "error"
                )
            raise
    
    def _create_data_panel(self) -> widgets.Widget:
        """Create the data management panel."""
        # Data upload section
        self._file_upload = widgets.FileUpload(
            accept='.csv,.xlsx,.json,.parquet',
            multiple=False,
            description='Upload Data'
        )
        self._file_upload.observe(self._on_file_upload, names='value')
        
        # Data info display
        self._data_info = widgets.HTML(
            value="<p>No data loaded</p>",
            layout=widgets.Layout(margin='10px 0')
        )
        
        # Manual data input option
        self._manual_data_input = widgets.Textarea(
            placeholder='Paste CSV data here...',
            layout=widgets.Layout(width='100%', height='200px')
        )
        
        self._load_manual_data_button = ActionButton(
            "Load Data",
            button_style='primary',
            icon='upload'
        )
        self._load_manual_data_button.add_click_callback(self._load_manual_data)
        
        # Sample data buttons
        self._load_sample_button = ActionButton(
            "Load Sample Data",
            button_style='info',
            icon='database'
        )
        self._load_sample_button.add_click_callback(self._load_sample_data)
        
        # Data actions
        self._refresh_button = ActionButton(
            "Refresh",
            button_style='secondary',
            icon='refresh'
        )
        self._refresh_button.add_click_callback(self._refresh_data)
        
        self._clear_data_button = ActionButton(
            "Clear Data",
            button_style='warning',
            icon='trash'
        )
        self._clear_data_button.add_click_callback(self._clear_data)
        
        # Export options
        self._export_data_button = ActionButton(
            "Export Data",
            button_style='success',
            icon='download'
        )
        self._export_data_button.add_click_callback(self._export_data)
        
        # Layout
        upload_section = widgets.VBox([
            widgets.HTML("<h4>Data Upload</h4>"),
            self._file_upload,
            widgets.HTML("<h5>Or paste data manually:</h5>"),
            self._manual_data_input,
            self._load_manual_data_button.widget
        ])
        
        actions_section = widgets.VBox([
            widgets.HTML("<h4>Data Actions</h4>"),
            widgets.HBox([
                self._load_sample_button.widget,
                self._refresh_button.widget,
                self._clear_data_button.widget,
                self._export_data_button.widget
            ])
        ])
        
        return widgets.VBox([
            widgets.HTML("<h3>Data Management</h3>"),
            self._data_info,
            upload_section,
            actions_section
        ])
    
    def _create_tabbed_interface(self) -> widgets.Widget:
        """Create the main tabbed interface."""
        # Create tabs
        tabs = widgets.Tab()
        
        # Tab content
        tab_children = [
            self._data_panel,
            self._filter_widget.widget,
            self._plotting_widget.widget,
            self._mapping_widget.widget
        ]
        
        tabs.children = tab_children
        
        # Tab titles
        tabs.set_title(0, '📊 Data')
        tabs.set_title(1, '🔍 Filters')
        tabs.set_title(2, '📈 Plots')
        tabs.set_title(3, '🗺️ Maps')
        
        # Main layout with header
        header = widgets.HTML(
            value="""
            <div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 20px;'>
                <h1 style='margin: 0; font-size: 2.5em;'>📊 DataVizTest</h1>
                <p style='margin: 10px 0 0 0; font-size: 1.2em;'>Modern Data Visualization and Analysis Toolkit</p>
            </div>
            """,
            layout=widgets.Layout(width='100%')
        )
        
        return widgets.VBox([
            header,
            self._message_display.widget,
            tabs
        ])
    
    def _setup_interactions(self) -> None:
        """Set up interactions between components."""
        # Connect state changes
        if self.app_service.state_manager:
            self.app_service.state_manager.add_callback("state_change", self._on_state_change)
    
    def _on_state_change(self, state) -> None:
        """Handle application state changes."""
        self._update_data_info()
        if self._message_display:
            self._message_display.show_message("Application state updated", "info")
    
    @handle_errors("file upload")
    def _on_file_upload(self, change: Dict[str, Any]) -> None:
        """Handle file upload."""
        if not change['new']:
            return
        
        try:
            # Get the uploaded file
            uploaded_file = list(change['new'].values())[0]
            content = uploaded_file['content']
            filename = uploaded_file['metadata']['name']
            
            self._message_display.show_message(f"Processing file: {filename}", "info")
            
            # Determine file type and load data
            if filename.endswith('.csv'):
                import io
                data = pd.read_csv(io.BytesIO(content))
            elif filename.endswith(('.xlsx', '.xls')):
                import io
                data = pd.read_excel(io.BytesIO(content))
            elif filename.endswith('.json'):
                import io
                data = pd.read_json(io.BytesIO(content))
            elif filename.endswith('.parquet'):
                import io
                data = pd.read_parquet(io.BytesIO(content))
            else:
                raise ValueError(f"Unsupported file type: {filename}")
            
            # Load data into application
            self.app_service.load_data(data)
            self._current_data = data
            
            self._message_display.show_message(
                f"Successfully loaded {data.shape[0]} rows and {data.shape[1]} columns from {filename}",
                "success"
            )
            
            # Clear the upload widget
            self._file_upload.value.clear()
            
        except Exception as e:
            self.logger.error(f"File upload failed: {e}")
            self._message_display.show_message(f"Failed to load file: {str(e)}", "error")
    
    @handle_errors("manual data loading")
    def _load_manual_data(self) -> None:
        """Load data from manual input."""
        if not self._manual_data_input.value.strip():
            self._message_display.show_message("Please paste some data first", "warning")
            return
        
        try:
            import io
            data = pd.read_csv(io.StringIO(self._manual_data_input.value))
            
            # Load data into application
            self.app_service.load_data(data)
            self._current_data = data
            
            self._message_display.show_message(
                f"Successfully loaded {data.shape[0]} rows and {data.shape[1]} columns",
                "success"
            )
            
            # Clear the input
            self._manual_data_input.value = ""
            
        except Exception as e:
            self.logger.error(f"Manual data loading failed: {e}")
            self._message_display.show_message(f"Failed to load data: {str(e)}", "error")
    
    @handle_errors("sample data loading")
    def _load_sample_data(self) -> None:
        """Load sample data for demonstration."""
        try:
            # Create sample dataset
            import numpy as np
            np.random.seed(42)
            
            n_samples = 100
            data = pd.DataFrame({
                'id': range(1, n_samples + 1),
                'name': [f'Item_{i}' for i in range(1, n_samples + 1)],
                'category': np.random.choice(['A', 'B', 'C', 'D'], n_samples),
                'value': np.random.normal(100, 25, n_samples),
                'score': np.random.uniform(0, 100, n_samples),
                'latitude': np.random.uniform(40.0, 41.0, n_samples),
                'longitude': np.random.uniform(-74.5, -73.5, n_samples),
                'date': pd.date_range('2023-01-01', periods=n_samples, freq='D'),
                'is_active': np.random.choice([True, False], n_samples)
            })
            
            # Load data into application
            self.app_service.load_data(data)
            self._current_data = data
            
            self._message_display.show_message(
                f"Successfully loaded sample dataset with {data.shape[0]} rows and {data.shape[1]} columns",
                "success"
            )
            
        except Exception as e:
            self.logger.error(f"Sample data loading failed: {e}")
            self._message_display.show_message(f"Failed to load sample data: {str(e)}", "error")
    
    def _refresh_data(self) -> None:
        """Refresh the current data display."""
        self._update_data_info()
        self._message_display.show_message("Data refreshed", "info")
    
    def _clear_data(self) -> None:
        """Clear all data."""
        self._current_data = None
        # Clear data in application service would go here
        self._update_data_info()
        self._message_display.show_message("Data cleared", "info")
    
    def _export_data(self) -> None:
        """Export current data."""
        if self._current_data is None:
            self._message_display.show_message("No data to export", "warning")
            return
        
        # In a real implementation, this would trigger a download
        self._message_display.show_message(
            "Export functionality would save data as CSV file",
            "info"
        )
    
    def _update_data_info(self) -> None:
        """Update the data information display."""
        if self._current_data is None:
            info_html = "<p style='color: #999;'>No data loaded</p>"
        else:
            data = self._current_data
            info_html = f"""
            <div style='background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;'>
                <h5 style='margin: 0 0 10px 0; color: #007bff;'>Dataset Overview</h5>
                <p style='margin: 5px 0;'><strong>Rows:</strong> {data.shape[0]:,}</p>
                <p style='margin: 5px 0;'><strong>Columns:</strong> {data.shape[1]}</p>
                <p style='margin: 5px 0;'><strong>Memory Usage:</strong> {data.memory_usage(deep=True).sum() / 1024**2:.2f} MB</p>
                <details style='margin-top: 10px;'>
                    <summary style='cursor: pointer; color: #007bff;'>Column Details</summary>
                    <ul style='margin: 10px 0; padding-left: 20px;'>
            """
            
            for col in data.columns:
                dtype = str(data[col].dtype)
                null_count = data[col].isnull().sum()
                info_html += f"<li><strong>{col}</strong>: {dtype} ({null_count} nulls)</li>"
            
            info_html += """
                    </ul>
                </details>
            </div>
            """
        
        if self._data_info:
            self._data_info.value = info_html
    
    @property
    def widget(self) -> Optional[widgets.Widget]:
        """Get the main widget for display."""
        return self._main_widget
    
    @property
    def is_initialized(self) -> bool:
        """Check if the interface is initialized."""
        return self._initialized
    
    def display(self) -> None:
        """Display the main interface."""
        if not self._initialized:
            self._create_interface()
        
        if self._main_widget:
            from IPython.display import display
            display(self._main_widget)
    
    def load_data(self, data: pd.DataFrame) -> None:
        """Load data programmatically."""
        self.app_service.load_data(data)
        self._current_data = data
        self._update_data_info()
        
        if self._message_display:
            self._message_display.show_message(
                f"Data loaded: {data.shape[0]} rows, {data.shape[1]} columns",
                "success"
            )
    
    def get_current_data(self) -> Optional[pd.DataFrame]:
        """Get the current dataset."""
        return self._current_data
    
    def create_plot(self, plot_config: PlotConfig) -> Any:
        """Create a plot programmatically."""
        return self.app_service.create_visualization(plot_config)
    
    def create_map(self, map_config: MapConfig) -> Any:
        """Create a map programmatically."""
        return self.app_service.create_map(map_config)
    
    def apply_filters(self, filter_set: FilterSet) -> pd.DataFrame:
        """Apply filters programmatically."""
        return self.app_service.apply_filters([filter_set])


# Convenience function to create and display the main interface
def create_interface(
    data: Optional[pd.DataFrame] = None,
    auto_display: bool = True
) -> MainUIController:
    """Create and optionally display the main DataVizTest interface.
    
    Args:
        data: Optional data to load initially
        auto_display: Whether to automatically display the interface
        
    Returns:
        MainUIController instance
    """
    controller = MainUIController(auto_display=auto_display)
    
    if data is not None:
        controller.load_data(data)
    
    if auto_display:
        controller.display()
    
    return controller