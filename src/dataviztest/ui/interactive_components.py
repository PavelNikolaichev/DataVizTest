"""Interactive components for DataVizTest UI.

This module provides common interactive UI patterns and components
used throughout the application.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Union

import ipywidgets as widgets
import pandas as pd
from IPython.display import display

from ..infrastructure import (
    get_logger,
    handle_errors,
    is_jupyter_environment,
)


class ProgressIndicator:
    """Progress indicator for long-running operations."""
    
    def __init__(self, description: str = "Processing..."):
        """Initialize progress indicator.
        
        Args:
            description: Description text to show
        """
        self.description = description
        self.logger = get_logger(__name__)
        
        # Create widgets
        self.progress_bar = widgets.FloatProgress(
            value=0,
            min=0,
            max=100,
            description=description,
            bar_style='info',
            style={'bar_color': '#0066cc'},
            layout=widgets.Layout(width='100%')
        )
        
        self.status_label = widgets.Label(value="Initializing...")
        
        self.container = widgets.VBox([
            self.progress_bar,
            self.status_label
        ])
        
        self._is_displayed = False
    
    def show(self) -> None:
        """Display the progress indicator."""
        if is_jupyter_environment() and not self._is_displayed:
            display(self.container)
            self._is_displayed = True
    
    def update(self, progress: float, status: str = "") -> None:
        """Update progress and status.
        
        Args:
            progress: Progress percentage (0-100)
            status: Status message
        """
        self.progress_bar.value = max(0, min(100, progress))
        if status:
            self.status_label.value = status
    
    def complete(self, message: str = "Complete!") -> None:
        """Mark as complete.
        
        Args:
            message: Completion message
        """
        self.progress_bar.value = 100
        self.progress_bar.bar_style = 'success'
        self.status_label.value = message
    
    def error(self, message: str = "Error occurred") -> None:
        """Mark as error.
        
        Args:
            message: Error message
        """
        self.progress_bar.bar_style = 'danger'
        self.status_label.value = message


class DataColumnSelector:
    """Widget for selecting data columns with type filtering."""
    
    def __init__(
        self,
        data: pd.DataFrame,
        column_types: Optional[List[str]] = None,
        multi_select: bool = False,
        description: str = "Select Column"
    ):
        """Initialize column selector.
        
        Args:
            data: DataFrame to select columns from
            column_types: Filter columns by type ('numeric', 'categorical', 'datetime')
            multi_select: Whether to allow multiple selections
            description: Widget description
        """
        self.data = data
        self.column_types = column_types or []
        self.multi_select = multi_select
        self.description = description
        self.logger = get_logger(__name__)
        
        # Get filtered columns
        self.available_columns = self._filter_columns()
        
        # Create widget
        if multi_select:
            self.selector = widgets.SelectMultiple(
                options=self.available_columns,
                description=description,
                layout=widgets.Layout(width='300px', height='120px')
            )
        else:
            self.selector = widgets.Dropdown(
                options=[('None', None)] + [(col, col) for col in self.available_columns],
                description=description,
                layout=widgets.Layout(width='300px')
            )
        
        # Callbacks
        self.on_change_callbacks: List[Callable] = []
        self.selector.observe(self._on_change, names='value')
    
    def _filter_columns(self) -> List[str]:
        """Filter columns based on specified types."""
        if not self.column_types:
            return list(self.data.columns)
        
        filtered_columns = []
        
        for col in self.data.columns:
            col_data = self.data[col]
            
            for col_type in self.column_types:
                if col_type == 'numeric' and pd.api.types.is_numeric_dtype(col_data):
                    filtered_columns.append(col)
                    break
                elif col_type == 'categorical' and (
                    pd.api.types.is_categorical_dtype(col_data) or 
                    pd.api.types.is_object_dtype(col_data)
                ):
                    filtered_columns.append(col)
                    break
                elif col_type == 'datetime' and pd.api.types.is_datetime64_any_dtype(col_data):
                    filtered_columns.append(col)
                    break
        
        return filtered_columns
    
    def _on_change(self, change: Dict[str, Any]) -> None:
        """Handle selection change."""
        for callback in self.on_change_callbacks:
            try:
                callback(change['new'])
            except Exception as e:
                self.logger.error(f"Error in column selector callback: {e}")
    
    def add_change_callback(self, callback: Callable) -> None:
        """Add callback for selection changes.
        
        Args:
            callback: Function to call when selection changes
        """
        self.on_change_callbacks.append(callback)
    
    @property
    def value(self) -> Union[str, List[str], None]:
        """Get selected value(s)."""
        return self.selector.value
    
    @value.setter
    def value(self, value: Union[str, List[str], None]) -> None:
        """Set selected value(s)."""
        self.selector.value = value
    
    @property
    def widget(self) -> widgets.Widget:
        """Get the widget."""
        return self.selector


class ValueRangeSelector:
    """Widget for selecting numeric value ranges."""
    
    def __init__(
        self,
        data: pd.Series,
        description: str = "Select Range"
    ):
        """Initialize range selector.
        
        Args:
            data: Numeric data series
            description: Widget description
        """
        self.data = data
        self.description = description
        self.logger = get_logger(__name__)
        
        # Calculate range
        self.min_value = float(data.min())
        self.max_value = float(data.max())
        
        # Create range slider
        self.range_slider = widgets.FloatRangeSlider(
            value=[self.min_value, self.max_value],
            min=self.min_value,
            max=self.max_value,
            step=(self.max_value - self.min_value) / 100,
            description=description,
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='.2f',
            layout=widgets.Layout(width='400px')
        )
        
        # Callbacks
        self.on_change_callbacks: List[Callable] = []
        self.range_slider.observe(self._on_change, names='value')
    
    def _on_change(self, change: Dict[str, Any]) -> None:
        """Handle range change."""
        for callback in self.on_change_callbacks:
            try:
                callback(change['new'])
            except Exception as e:
                self.logger.error(f"Error in range selector callback: {e}")
    
    def add_change_callback(self, callback: Callable) -> None:
        """Add callback for range changes.
        
        Args:
            callback: Function to call when range changes
        """
        self.on_change_callbacks.append(callback)
    
    @property
    def value(self) -> tuple:
        """Get selected range."""
        return self.range_slider.value
    
    @value.setter
    def value(self, value: tuple) -> None:
        """Set selected range."""
        self.range_slider.value = value
    
    @property
    def widget(self) -> widgets.Widget:
        """Get the widget."""
        return self.range_slider


class CategorySelector:
    """Widget for selecting categorical values."""
    
    def __init__(
        self,
        categories: List[str],
        description: str = "Select Categories",
        max_items: int = 10
    ):
        """Initialize category selector.
        
        Args:
            categories: List of category options
            description: Widget description
            max_items: Maximum number of items to show
        """
        self.categories = categories[:max_items]  # Limit for performance
        self.description = description
        self.logger = get_logger(__name__)
        
        # Create selection widget
        self.selector = widgets.SelectMultiple(
            options=self.categories,
            value=self.categories,  # Select all by default
            description=description,
            layout=widgets.Layout(width='300px', height='150px')
        )
        
        # Callbacks
        self.on_change_callbacks: List[Callable] = []
        self.selector.observe(self._on_change, names='value')
    
    def _on_change(self, change: Dict[str, Any]) -> None:
        """Handle selection change."""
        for callback in self.on_change_callbacks:
            try:
                callback(list(change['new']))
            except Exception as e:
                self.logger.error(f"Error in category selector callback: {e}")
    
    def add_change_callback(self, callback: Callable) -> None:
        """Add callback for selection changes.
        
        Args:
            callback: Function to call when selection changes
        """
        self.on_change_callbacks.append(callback)
    
    @property
    def value(self) -> List[str]:
        """Get selected categories."""
        return list(self.selector.value)
    
    @value.setter
    def value(self, value: List[str]) -> None:
        """Set selected categories."""
        self.selector.value = value
    
    @property
    def widget(self) -> widgets.Widget:
        """Get the widget."""
        return self.selector


class ActionButton:
    """Customizable action button with progress indication."""
    
    def __init__(
        self,
        description: str,
        button_style: str = 'primary',
        icon: str = '',
        tooltip: str = ''
    ):
        """Initialize action button.
        
        Args:
            description: Button text
            button_style: Button style ('primary', 'success', 'info', 'warning', 'danger')
            icon: Font Awesome icon name
            tooltip: Tooltip text
        """
        self.description = description
        self.button_style = button_style
        self.icon = icon
        self.tooltip = tooltip
        self.logger = get_logger(__name__)
        
        # Create button
        self.button = widgets.Button(
            description=description,
            button_style=button_style,
            icon=icon,
            tooltip=tooltip,
            layout=widgets.Layout(width='auto', margin='2px')
        )
        
        # State tracking
        self._original_description = description
        self._is_processing = False
        
        # Callbacks
        self.click_callbacks: List[Callable] = []
        self.button.on_click(self._on_click)
    
    def _on_click(self, button: widgets.Button) -> None:
        """Handle button click."""
        if self._is_processing:
            return  # Prevent multiple clicks
        
        for callback in self.click_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in button callback: {e}")
    
    def add_click_callback(self, callback: Callable) -> None:
        """Add callback for button clicks.
        
        Args:
            callback: Function to call when button is clicked
        """
        self.click_callbacks.append(callback)
    
    def set_processing(self, processing: bool = True) -> None:
        """Set processing state.
        
        Args:
            processing: Whether button is processing
        """
        self._is_processing = processing
        
        if processing:
            self.button.description = "Processing..."
            self.button.icon = "spinner fa-spin"
            self.button.disabled = True
        else:
            self.button.description = self._original_description
            self.button.icon = self.icon
            self.button.disabled = False
    
    @property
    def widget(self) -> widgets.Widget:
        """Get the button widget."""
        return self.button


class MessageDisplay:
    """Widget for displaying status messages."""
    
    def __init__(self):
        """Initialize message display."""
        self.logger = get_logger(__name__)
        
        # Create HTML widget for messages
        self.html_widget = widgets.HTML(
            value="",
            layout=widgets.Layout(
                width='100%',
                margin='5px 0px',
                padding='10px',
                border='1px solid #ddd',
                border_radius='4px'
            )
        )
        
        self._messages: List[Dict[str, str]] = []
        self._max_messages = 5
    
    def show_message(
        self, 
        message: str, 
        message_type: str = "info",
        auto_hide: bool = True
    ) -> None:
        """Show a message.
        
        Args:
            message: Message text
            message_type: Message type ('info', 'warning', 'error', 'success')
            auto_hide: Whether to auto-hide after some time
        """
        # Add to messages list
        self._messages.append({
            'text': message,
            'type': message_type,
            'timestamp': pd.Timestamp.now().strftime('%H:%M:%S')
        })
        
        # Keep only recent messages
        if len(self._messages) > self._max_messages:
            self._messages.pop(0)
        
        # Update display
        self._update_display()
        
        # Auto-hide for info messages
        if auto_hide and message_type == 'info':
            asyncio.create_task(self._auto_hide_message())
    
    async def _auto_hide_message(self) -> None:
        """Auto-hide message after delay."""
        await asyncio.sleep(3)  # Hide after 3 seconds
        if self._messages:
            self._messages.pop(0)
            self._update_display()
    
    def _update_display(self) -> None:
        """Update the HTML display."""
        if not self._messages:
            self.html_widget.value = ""
            return
        
        # Color mapping
        color_map = {
            'info': '#d1ecf1',
            'warning': '#fff3cd',
            'error': '#f8d7da',
            'success': '#d4edda'
        }
        
        # Text color mapping
        text_color_map = {
            'info': '#0c5460',
            'warning': '#856404',
            'error': '#721c24',
            'success': '#155724'
        }
        
        # Build HTML
        html_parts = []
        for msg in self._messages[-3:]:  # Show only last 3 messages
            bg_color = color_map.get(msg['type'], '#f8f9fa')
            text_color = text_color_map.get(msg['type'], '#333')
            
            html_parts.append(f"""
                <div style="
                    background-color: {bg_color};
                    color: {text_color};
                    padding: 8px 12px;
                    margin: 2px 0;
                    border-radius: 4px;
                    font-size: 14px;
                ">
                    <span style="font-weight: bold;">[{msg['timestamp']}]</span> {msg['text']}
                </div>
            """)
        
        self.html_widget.value = "".join(html_parts)
    
    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._update_display()
    
    @property
    def widget(self) -> widgets.Widget:
        """Get the message display widget."""
        return self.html_widget