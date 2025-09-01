"""Filter widget for interactive data filtering.

This module provides a comprehensive filtering interface that allows
users to create and apply various types of filters to their data.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import ipywidgets as widgets
import pandas as pd

from .base_widget import InteractiveWidget
from ..interactive_components import (
    DataColumnSelector,
    ValueRangeSelector,
    CategorySelector,
    ActionButton,
    MessageDisplay
)
from ...infrastructure import get_logger, handle_errors
from ...models import (
    FilterSet,
    NumericFilter,
    CategoricalFilter,
    TextFilter,
    FilterOperator,
    FilterType,
)
from ...services import ApplicationService


class FilterWidget(InteractiveWidget):
    """Widget for creating and managing data filters."""
    
    def __init__(
        self,
        app_service: Optional[ApplicationService] = None,
        **kwargs
    ):
        """Initialize the filter widget.
        
        Args:
            app_service: Application service for data operations
            **kwargs: Additional widget arguments
        """
        super().__init__(app_service=app_service, **kwargs)
        
        # Filter state
        self._current_filter_set: Optional[FilterSet] = None
        self._active_filters: List[Any] = []
        
        # UI components
        self._filter_type_selector: Optional[widgets.Dropdown] = None
        self._column_selector: Optional[DataColumnSelector] = None
        self._filter_controls: Optional[widgets.Widget] = None
        self._filter_list: Optional[widgets.VBox] = None
        self._message_display: Optional[MessageDisplay] = None
        
        self.logger = get_logger(__name__)
    
    def _create_widget(self) -> widgets.Widget:
        """Create the filter widget interface."""
        # Title
        title = widgets.HTML("<h3>Data Filters</h3>")
        
        # Message display
        self._message_display = MessageDisplay()
        
        # Filter type selector
        self._filter_type_selector = widgets.Dropdown(
            options=[
                ('Numeric Range', 'numeric'),
                ('Category Selection', 'categorical'), 
                ('Text Search', 'text')
            ],
            description='Filter Type:',
            layout=widgets.Layout(width='300px')
        )
        self._filter_type_selector.observe(self._on_filter_type_change, names='value')
        
        # Column selector (will be populated when data is available)
        self._column_selector_container = widgets.VBox()
        
        # Filter controls container
        self._filter_controls = widgets.VBox()
        
        # Action buttons
        self._add_filter_button = ActionButton(
            "Add Filter",
            button_style='primary',
            icon='plus'
        )
        self._add_filter_button.add_click_callback(self._add_filter)
        
        self._apply_filters_button = ActionButton(
            "Apply Filters",
            button_style='success',
            icon='check'
        )
        self._apply_filters_button.add_click_callback(self._apply_filters)
        
        self._clear_filters_button = ActionButton(
            "Clear All",
            button_style='warning',
            icon='trash'
        )
        self._clear_filters_button.add_click_callback(self._clear_filters)
        
        # Active filters list
        self._filter_list = widgets.VBox()
        
        # Layout
        filter_creation = widgets.VBox([
            widgets.HTML("<h4>Create New Filter</h4>"),
            self._filter_type_selector,
            self._column_selector_container,
            self._filter_controls,
            widgets.HBox([
                self._add_filter_button.widget,
                self._apply_filters_button.widget,
                self._clear_filters_button.widget
            ])
        ])
        
        active_filters_section = widgets.VBox([
            widgets.HTML("<h4>Active Filters</h4>"),
            self._filter_list
        ])
        
        return widgets.VBox([
            title,
            self._message_display.widget,
            filter_creation,
            active_filters_section
        ])
    
    def _setup_interactions(self) -> None:
        """Set up widget interactions."""
        # Update interface when data changes
        if self.app_service:
            self.add_callback("state_change", self._on_data_change)
    
    def _on_data_change(self, state) -> None:
        """Handle data changes."""
        current_data = self.app_service.current_data
        if current_data is not None:
            self._update_column_selector()
            self._message_display.show_message(
                f"Data updated: {current_data.shape[0]} rows, {current_data.shape[1]} columns",
                "info"
            )
    
    def _update_column_selector(self) -> None:
        """Update the column selector based on current data and filter type."""
        if not self.app_service or self.app_service.current_data is None:
            return
        
        data = self.app_service.current_data
        filter_type = self._filter_type_selector.value if self._filter_type_selector else 'numeric'
        
        # Determine column types to show
        if filter_type == 'numeric':
            column_types = ['numeric']
        elif filter_type == 'categorical':
            column_types = ['categorical']
        elif filter_type == 'text':
            column_types = ['categorical', 'text']  # Both text and categorical for text filters
        else:
            column_types = []
        
        # Create new column selector
        self._column_selector = DataColumnSelector(
            data=data,
            column_types=column_types,
            description="Column:",
            multi_select=False
        )
        self._column_selector.add_change_callback(self._on_column_change)
        
        # Update container
        self._column_selector_container.children = [self._column_selector.widget]
    
    def _on_filter_type_change(self, change: Dict[str, Any]) -> None:
        """Handle filter type change."""
        self._update_column_selector()
        self._update_filter_controls()
    
    def _on_column_change(self, column_name: str) -> None:
        """Handle column selection change."""
        self._update_filter_controls()
    
    def _update_filter_controls(self) -> None:
        """Update filter controls based on selected type and column."""
        if (not self._filter_type_selector or 
            not self._column_selector or 
            not self._column_selector.value or
            not self.app_service or 
            self.app_service.current_data is None):
            self._filter_controls.children = []
            return
        
        filter_type = self._filter_type_selector.value
        column_name = self._column_selector.value
        data = self.app_service.current_data
        
        if column_name not in data.columns:
            self._filter_controls.children = []
            return
        
        column_data = data[column_name]
        
        # Create appropriate controls based on filter type
        if filter_type == 'numeric':
            self._create_numeric_controls(column_data)
        elif filter_type == 'categorical':
            self._create_categorical_controls(column_data)
        elif filter_type == 'text':
            self._create_text_controls()
    
    def _create_numeric_controls(self, data: pd.Series) -> None:
        """Create controls for numeric filtering."""
        try:
            # Range selector
            range_selector = ValueRangeSelector(
                data=data,
                description="Value Range:"
            )
            
            # Operator selector
            operator_selector = widgets.Dropdown(
                options=[
                    ('Between', FilterOperator.BETWEEN),
                    ('Greater than', FilterOperator.GREATER_THAN),
                    ('Less than', FilterOperator.LESS_THAN),
                    ('Equals', FilterOperator.EQUALS)
                ],
                value=FilterOperator.BETWEEN,
                description='Operator:',
                layout=widgets.Layout(width='200px')
            )
            
            self._filter_controls.children = [
                operator_selector,
                range_selector.widget
            ]
            
            # Store references for later use
            self._numeric_operator = operator_selector
            self._numeric_range = range_selector
            
        except Exception as e:
            self.logger.error(f"Error creating numeric controls: {e}")
            self._filter_controls.children = [
                widgets.HTML(f"<div style='color: red;'>Error: {str(e)}</div>")
            ]
    
    def _create_categorical_controls(self, data: pd.Series) -> None:
        """Create controls for categorical filtering."""
        try:
            # Get unique categories
            categories = data.dropna().unique().tolist()
            
            # Category selector
            category_selector = CategorySelector(
                categories=categories,
                description="Categories:",
                max_items=20  # Limit for performance
            )
            
            # Include/Exclude selector
            include_exclude = widgets.Dropdown(
                options=[
                    ('Include selected', False),
                    ('Exclude selected', True)
                ],
                value=False,
                description='Mode:',
                layout=widgets.Layout(width='200px')
            )
            
            self._filter_controls.children = [
                include_exclude,
                category_selector.widget
            ]
            
            # Store references
            self._categorical_mode = include_exclude
            self._categorical_selector = category_selector
            
        except Exception as e:
            self.logger.error(f"Error creating categorical controls: {e}")
            self._filter_controls.children = [
                widgets.HTML(f"<div style='color: red;'>Error: {str(e)}</div>")
            ]
    
    def _create_text_controls(self) -> None:
        """Create controls for text filtering."""
        # Text input
        text_input = widgets.Text(
            placeholder="Enter search text...",
            description="Search:",
            layout=widgets.Layout(width='300px')
        )
        
        # Operator selector
        operator_selector = widgets.Dropdown(
            options=[
                ('Contains', FilterOperator.CONTAINS),
                ('Starts with', FilterOperator.STARTS_WITH),
                ('Ends with', FilterOperator.ENDS_WITH),
                ('Equals', FilterOperator.EQUALS)
            ],
            value=FilterOperator.CONTAINS,
            description='Match:',
            layout=widgets.Layout(width='200px')
        )
        
        # Case sensitivity
        case_sensitive = widgets.Checkbox(
            value=False,
            description='Case sensitive'
        )
        
        self._filter_controls.children = [
            operator_selector,
            text_input,
            case_sensitive
        ]
        
        # Store references
        self._text_operator = operator_selector
        self._text_input = text_input
        self._text_case_sensitive = case_sensitive
    
    @handle_errors("filter addition")
    def _add_filter(self) -> None:
        """Add a new filter based on current settings."""
        if (not self._filter_type_selector or 
            not self._column_selector or 
            not self._column_selector.value):
            self._message_display.show_message("Please select filter type and column", "warning")
            return
        
        filter_type = self._filter_type_selector.value
        column_name = self._column_selector.value
        
        try:
            # Create filter based on type
            if filter_type == 'numeric':
                filter_obj = self._create_numeric_filter(column_name)
            elif filter_type == 'categorical':
                filter_obj = self._create_categorical_filter(column_name)
            elif filter_type == 'text':
                filter_obj = self._create_text_filter(column_name)
            else:
                self._message_display.show_message("Unknown filter type", "error")
                return
            
            if filter_obj:
                self._active_filters.append(filter_obj)
                self._update_filter_list()
                self._message_display.show_message(f"Added {filter_type} filter for {column_name}", "success")
        
        except Exception as e:
            self.logger.error(f"Error adding filter: {e}")
            self._message_display.show_message(f"Error adding filter: {str(e)}", "error")
    
    def _create_numeric_filter(self, column_name: str) -> Optional[NumericFilter]:
        """Create a numeric filter."""
        if not hasattr(self, '_numeric_operator') or not hasattr(self, '_numeric_range'):
            return None
        
        operator = self._numeric_operator.value
        range_value = self._numeric_range.value
        
        if operator == FilterOperator.BETWEEN:
            return NumericFilter(
                name=f"{column_name} between {range_value[0]:.2f} and {range_value[1]:.2f}",
                column=column_name,
                operator=operator,
                min_value=range_value[0],
                max_value=range_value[1]
            )
        else:
            # For other operators, use the appropriate value
            value = range_value[0] if operator in [FilterOperator.GREATER_THAN, FilterOperator.EQUALS] else range_value[1]
            return NumericFilter(
                name=f"{column_name} {operator.value} {value:.2f}",
                column=column_name,
                operator=operator,
                min_value=value if operator in [FilterOperator.GREATER_THAN, FilterOperator.EQUALS] else None,
                max_value=value if operator == FilterOperator.LESS_THAN else None
            )
    
    def _create_categorical_filter(self, column_name: str) -> Optional[CategoricalFilter]:
        """Create a categorical filter."""
        if not hasattr(self, '_categorical_selector') or not hasattr(self, '_categorical_mode'):
            return None
        
        selected_values = self._categorical_selector.value
        exclude_mode = self._categorical_mode.value
        
        if not selected_values:
            return None
        
        operator = FilterOperator.NOT_IN if exclude_mode else FilterOperator.IN
        mode_text = "exclude" if exclude_mode else "include"
        
        return CategoricalFilter(
            name=f"{column_name} {mode_text} {len(selected_values)} values",
            column=column_name,
            operator=operator,
            selected_values=selected_values,
            exclude_mode=exclude_mode
        )
    
    def _create_text_filter(self, column_name: str) -> Optional[TextFilter]:
        """Create a text filter."""
        if (not hasattr(self, '_text_input') or 
            not hasattr(self, '_text_operator') or 
            not hasattr(self, '_text_case_sensitive')):
            return None
        
        text_value = self._text_input.value.strip()
        if not text_value:
            return None
        
        operator = self._text_operator.value
        case_sensitive = self._text_case_sensitive.value
        
        return TextFilter(
            name=f"{column_name} {operator.value} '{text_value}'",
            column=column_name,
            operator=operator,
            text_value=text_value,
            case_sensitive=case_sensitive
        )
    
    def _update_filter_list(self) -> None:
        """Update the display of active filters."""
        if not self._filter_list:
            return
        
        if not self._active_filters:
            self._filter_list.children = [
                widgets.HTML("<i>No active filters</i>")
            ]
            return
        
        filter_widgets = []
        for i, filter_obj in enumerate(self._active_filters):
            # Create filter display
            filter_html = widgets.HTML(
                f"<div style='padding: 5px; border: 1px solid #ddd; margin: 2px; border-radius: 3px;'>"
                f"<b>{filter_obj.name}</b>"
                f"</div>"
            )
            
            # Remove button
            remove_button = ActionButton(
                "Remove",
                button_style='danger',
                icon='trash'
            )
            remove_button.add_click_callback(lambda i=i: self._remove_filter(i))
            
            filter_widgets.append(
                widgets.HBox([filter_html, remove_button.widget])
            )
        
        self._filter_list.children = filter_widgets
    
    def _remove_filter(self, index: int) -> None:
        """Remove a filter by index."""
        if 0 <= index < len(self._active_filters):
            removed_filter = self._active_filters.pop(index)
            self._update_filter_list()
            self._message_display.show_message(f"Removed filter: {removed_filter.name}", "info")
    
    @handle_errors("filter application")
    def _apply_filters(self) -> None:
        """Apply all active filters."""
        if not self.app_service:
            self._message_display.show_message("No application service available", "error")
            return
        
        if not self._active_filters:
            self._message_display.show_message("No filters to apply", "warning")
            return
        
        try:
            # Create filter set
            filter_set = FilterSet(name=f"Filter Set {len(self._active_filters)} filters")
            for filter_obj in self._active_filters:
                filter_set.add_filter(filter_obj)
            
            # Apply filters through application service
            result = self.app_service.apply_filters([filter_set])
            
            # Show result
            retention_rate = (result.filtered_row_count / result.original_row_count) * 100
            self._message_display.show_message(
                f"Filters applied: {result.original_row_count} → {result.filtered_row_count} rows "
                f"({retention_rate:.1f}% retained)",
                "success"
            )
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {e}")
            self._message_display.show_message(f"Error applying filters: {str(e)}", "error")
    
    def _clear_filters(self) -> None:
        """Clear all active filters."""
        self._active_filters.clear()
        self._update_filter_list()
        self._message_display.show_message("All filters cleared", "info")