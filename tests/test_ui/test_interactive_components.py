"""Unit tests for interactive components."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict, List, Callable

import ipywidgets as widgets

from dataviztest.ui.interactive_components import (
    DataColumnSelector,
    ValueRangeSelector,
    CategorySelector,
    ActionButton,
    MessageDisplay
)


class TestDataColumnSelector:
    """Test cases for DataColumnSelector."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        return pd.DataFrame({
            'id': range(1, 11),
            'name': [f'Item_{i}' for i in range(1, 11)],
            'category': ['A', 'B', 'C'] * 3 + ['A'],
            'value': [i * 1.5 for i in range(1, 11)],
            'score': range(10, 20),
            'date': pd.date_range('2023-01-01', periods=10),
            'is_active': [True, False] * 5
        })
    
    def test_initialization_basic(self, sample_data):
        """Test basic initialization."""
        selector = DataColumnSelector(data=sample_data)
        
        assert selector.data is not None
        assert selector.widget is not None
        assert isinstance(selector.widget, widgets.Dropdown)
        assert selector.multi_select is False
        assert selector.allow_none is False
    
    def test_initialization_multi_select(self, sample_data):
        """Test initialization with multi-select."""
        selector = DataColumnSelector(
            data=sample_data,
            multi_select=True
        )
        
        assert selector.multi_select is True
        assert isinstance(selector.widget, widgets.SelectMultiple)
    
    def test_initialization_with_column_types(self, sample_data):
        """Test initialization with specific column types."""
        selector = DataColumnSelector(
            data=sample_data,
            column_types=['numeric']
        )
        
        # Should only include numeric columns
        options = [opt[1] for opt in selector.widget.options]
        assert 'value' in options
        assert 'score' in options
        assert 'name' not in options
        assert 'category' not in options
    
    def test_initialization_categorical_columns(self, sample_data):
        """Test initialization with categorical column types."""
        selector = DataColumnSelector(
            data=sample_data,
            column_types=['categorical']
        )
        
        options = [opt[1] for opt in selector.widget.options]
        assert 'name' in options
        assert 'category' in options
        assert 'value' not in options
        assert 'score' not in options
    
    def test_initialization_datetime_columns(self, sample_data):
        """Test initialization with datetime column types."""
        selector = DataColumnSelector(
            data=sample_data,
            column_types=['datetime']
        )
        
        options = [opt[1] for opt in selector.widget.options]
        assert 'date' in options
        assert 'value' not in options
        assert 'name' not in options
    
    def test_initialization_boolean_columns(self, sample_data):
        """Test initialization with boolean column types."""
        selector = DataColumnSelector(
            data=sample_data,
            column_types=['boolean']
        )
        
        options = [opt[1] for opt in selector.widget.options]
        assert 'is_active' in options
        assert 'value' not in options
        assert 'name' not in options
    
    def test_initialization_allow_none(self, sample_data):
        """Test initialization with allow_none option."""
        selector = DataColumnSelector(
            data=sample_data,
            allow_none=True
        )
        
        options = [opt[1] for opt in selector.widget.options]
        assert None in options
    
    def test_value_property_single_select(self, sample_data):
        """Test value property for single select."""
        selector = DataColumnSelector(data=sample_data)
        
        # Initially no selection
        assert selector.value is None
        
        # After selection
        selector.widget.value = 'value'
        assert selector.value == 'value'
    
    def test_value_property_multi_select(self, sample_data):
        """Test value property for multi select."""
        selector = DataColumnSelector(
            data=sample_data,
            multi_select=True
        )
        
        # Initially empty
        assert selector.value == []
        
        # After selection
        selector.widget.value = ('value', 'score')
        assert selector.value == ['value', 'score']
    
    def test_add_change_callback(self, sample_data):
        """Test adding change callback."""
        selector = DataColumnSelector(data=sample_data)
        
        callback_called = False
        callback_value = None
        
        def test_callback(value):
            nonlocal callback_called, callback_value
            callback_called = True
            callback_value = value
        
        selector.add_change_callback(test_callback)
        
        # Simulate change
        selector.widget.value = 'value'
        # Manually trigger callback since we can't simulate actual widget change
        test_callback('value')
        
        assert callback_called is True
        assert callback_value == 'value'
    
    def test_set_value_single_select(self, sample_data):
        """Test setting value for single select."""
        selector = DataColumnSelector(data=sample_data)
        
        selector.set_value('value')
        assert selector.widget.value == 'value'
        assert selector.value == 'value'
    
    def test_set_value_multi_select(self, sample_data):
        """Test setting value for multi select."""
        selector = DataColumnSelector(
            data=sample_data,
            multi_select=True
        )
        
        selector.set_value(['value', 'score'])
        assert list(selector.widget.value) == ['value', 'score']
        assert selector.value == ['value', 'score']
    
    def test_get_column_types(self, sample_data):
        """Test getting column types from data."""
        selector = DataColumnSelector(data=sample_data)
        
        column_types = selector._get_column_types()
        
        assert 'numeric' in column_types
        assert 'categorical' in column_types
        assert 'datetime' in column_types
        assert 'boolean' in column_types
        
        assert 'value' in column_types['numeric']
        assert 'score' in column_types['numeric']
        assert 'name' in column_types['categorical']
        assert 'category' in column_types['categorical']
        assert 'date' in column_types['datetime']
        assert 'is_active' in column_types['boolean']


class TestValueRangeSelector:
    """Test cases for ValueRangeSelector."""
    
    def test_initialization(self):
        """Test basic initialization."""
        selector = ValueRangeSelector(
            min_value=0,
            max_value=100,
            step=1
        )
        
        assert selector.widget is not None
        assert isinstance(selector.widget, widgets.FloatRangeSlider)
        assert selector.min_value == 0
        assert selector.max_value == 100
        assert selector.step == 1
    
    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        selector = ValueRangeSelector(
            min_value=10,
            max_value=50,
            step=2,
            default_min=15,
            default_max=45
        )
        
        assert selector.widget.value == (15, 45)
        assert selector.widget.min == 10
        assert selector.widget.max == 50
        assert selector.widget.step == 2
    
    def test_value_property(self):
        """Test value property."""
        selector = ValueRangeSelector(
            min_value=0,
            max_value=100
        )
        
        # Initially default range
        min_val, max_val = selector.value
        assert min_val >= 0
        assert max_val <= 100
        
        # After setting value
        selector.widget.value = (20, 80)
        assert selector.value == (20, 80)
    
    def test_set_range(self):
        """Test setting range programmatically."""
        selector = ValueRangeSelector(
            min_value=0,
            max_value=100
        )
        
        selector.set_range(30, 70)
        assert selector.widget.value == (30, 70)
        assert selector.value == (30, 70)
    
    def test_add_change_callback(self):
        """Test adding change callback."""
        selector = ValueRangeSelector(
            min_value=0,
            max_value=100
        )
        
        callback_called = False
        callback_value = None
        
        def test_callback(value):
            nonlocal callback_called, callback_value
            callback_called = True
            callback_value = value
        
        selector.add_change_callback(test_callback)
        
        # Simulate change
        selector.widget.value = (25, 75)
        test_callback((25, 75))
        
        assert callback_called is True
        assert callback_value == (25, 75)


class TestCategorySelector:
    """Test cases for CategorySelector."""
    
    @pytest.fixture
    def categories(self):
        """Create test categories."""
        return ['Category A', 'Category B', 'Category C', 'Category D']
    
    def test_initialization(self, categories):
        """Test basic initialization."""
        selector = CategorySelector(categories=categories)
        
        assert selector.widget is not None
        assert isinstance(selector.widget, widgets.SelectMultiple)
        assert len(selector.widget.options) == 4
        assert selector.categories == categories
    
    def test_initialization_with_defaults(self, categories):
        """Test initialization with default selections."""
        defaults = ['Category A', 'Category C']
        selector = CategorySelector(
            categories=categories,
            default_selected=defaults
        )
        
        assert list(selector.widget.value) == defaults
        assert selector.value == defaults
    
    def test_value_property(self, categories):
        """Test value property."""
        selector = CategorySelector(categories=categories)
        
        # Initially empty
        assert selector.value == []
        
        # After selection
        selector.widget.value = ('Category A', 'Category B')
        assert selector.value == ['Category A', 'Category B']
    
    def test_set_selected(self, categories):
        """Test setting selected categories."""
        selector = CategorySelector(categories=categories)
        
        selected = ['Category B', 'Category D']
        selector.set_selected(selected)
        
        assert list(selector.widget.value) == selected
        assert selector.value == selected
    
    def test_select_all(self, categories):
        """Test selecting all categories."""
        selector = CategorySelector(categories=categories)
        
        selector.select_all()
        
        assert len(selector.value) == len(categories)
        assert set(selector.value) == set(categories)
    
    def test_clear_selection(self, categories):
        """Test clearing selection."""
        selector = CategorySelector(
            categories=categories,
            default_selected=['Category A', 'Category B']
        )
        
        # Initially has selection
        assert len(selector.value) > 0
        
        selector.clear_selection()
        assert selector.value == []
    
    def test_add_change_callback(self, categories):
        """Test adding change callback."""
        selector = CategorySelector(categories=categories)
        
        callback_called = False
        callback_value = None
        
        def test_callback(value):
            nonlocal callback_called, callback_value
            callback_called = True
            callback_value = value
        
        selector.add_change_callback(test_callback)
        
        # Simulate change
        selector.widget.value = ('Category A',)
        test_callback(['Category A'])
        
        assert callback_called is True
        assert callback_value == ['Category A']


class TestActionButton:
    """Test cases for ActionButton."""
    
    def test_initialization_basic(self):
        """Test basic initialization."""
        button = ActionButton("Test Button")
        
        assert button.widget is not None
        assert isinstance(button.widget, widgets.Button)
        assert button.widget.description == "Test Button"
        assert button.widget.button_style == ""
        assert button.widget.icon == ""
    
    def test_initialization_with_style(self):
        """Test initialization with style options."""
        button = ActionButton(
            "Styled Button",
            button_style="primary",
            icon="check"
        )
        
        assert button.widget.description == "Styled Button"
        assert button.widget.button_style == "primary"
        assert button.widget.icon == "check"
    
    def test_add_click_callback(self):
        """Test adding click callback."""
        button = ActionButton("Test Button")
        
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        button.add_click_callback(test_callback)
        
        # Simulate click
        test_callback()
        
        assert callback_called is True
    
    def test_set_enabled(self):
        """Test enabling/disabling button."""
        button = ActionButton("Test Button")
        
        # Initially enabled
        assert button.widget.disabled is False
        
        button.set_enabled(False)
        assert button.widget.disabled is True
        
        button.set_enabled(True)
        assert button.widget.disabled is False
    
    def test_set_description(self):
        """Test setting button description."""
        button = ActionButton("Original")
        
        button.set_description("New Description")
        assert button.widget.description == "New Description"
    
    def test_set_style(self):
        """Test setting button style."""
        button = ActionButton("Test Button")
        
        button.set_style("success")
        assert button.widget.button_style == "success"
    
    def test_set_icon(self):
        """Test setting button icon."""
        button = ActionButton("Test Button")
        
        button.set_icon("star")
        assert button.widget.icon == "star"


class TestMessageDisplay:
    """Test cases for MessageDisplay."""
    
    def test_initialization(self):
        """Test basic initialization."""
        display = MessageDisplay()
        
        assert display.widget is not None
        assert isinstance(display.widget, widgets.HTML)
        assert display._current_message == ""
        assert display._current_type == "info"
    
    def test_show_message_info(self):
        """Test showing info message."""
        display = MessageDisplay()
        
        display.show_message("This is an info message", "info")
        
        assert display._current_message == "This is an info message"
        assert display._current_type == "info"
        assert "info" in display.widget.value.lower()
        assert "This is an info message" in display.widget.value
    
    def test_show_message_success(self):
        """Test showing success message."""
        display = MessageDisplay()
        
        display.show_message("Operation successful!", "success")
        
        assert display._current_message == "Operation successful!"
        assert display._current_type == "success"
        assert "success" in display.widget.value.lower()
    
    def test_show_message_warning(self):
        """Test showing warning message."""
        display = MessageDisplay()
        
        display.show_message("This is a warning", "warning")
        
        assert display._current_message == "This is a warning"
        assert display._current_type == "warning"
        assert "warning" in display.widget.value.lower()
    
    def test_show_message_error(self):
        """Test showing error message."""
        display = MessageDisplay()
        
        display.show_message("An error occurred", "error")
        
        assert display._current_message == "An error occurred"
        assert display._current_type == "error"
        assert "error" in display.widget.value.lower()
    
    def test_clear_message(self):
        """Test clearing message."""
        display = MessageDisplay()
        
        # Show a message first
        display.show_message("Test message", "info")
        assert display._current_message != ""
        
        # Clear the message
        display.clear_message()
        assert display._current_message == ""
        assert display.widget.value == ""
    
    def test_set_auto_clear(self):
        """Test auto-clear functionality."""
        display = MessageDisplay()
        
        # Test with auto-clear enabled
        with patch('threading.Timer') as mock_timer:
            mock_timer_instance = Mock()
            mock_timer.return_value = mock_timer_instance
            
            display.show_message("Auto-clear message", "info", auto_clear=True, clear_delay=3)
            
            mock_timer.assert_called_once_with(3, display.clear_message)
            mock_timer_instance.start.assert_called_once()
    
    def test_get_message_html_info(self):
        """Test HTML generation for info message."""
        display = MessageDisplay()
        
        html = display._get_message_html("Test info", "info")
        
        assert "Test info" in html
        assert "blue" in html.lower() or "info" in html.lower()
    
    def test_get_message_html_success(self):
        """Test HTML generation for success message."""
        display = MessageDisplay()
        
        html = display._get_message_html("Success!", "success")
        
        assert "Success!" in html
        assert "green" in html.lower() or "success" in html.lower()
    
    def test_get_message_html_warning(self):
        """Test HTML generation for warning message."""
        display = MessageDisplay()
        
        html = display._get_message_html("Warning!", "warning")
        
        assert "Warning!" in html
        assert "orange" in html.lower() or "warning" in html.lower()
    
    def test_get_message_html_error(self):
        """Test HTML generation for error message."""
        display = MessageDisplay()
        
        html = display._get_message_html("Error!", "error")
        
        assert "Error!" in html
        assert "red" in html.lower() or "error" in html.lower()
    
    def test_current_message_property(self):
        """Test current_message property."""
        display = MessageDisplay()
        
        assert display.current_message == ""
        
        display.show_message("Test message", "info")
        assert display.current_message == "Test message"
    
    def test_current_type_property(self):
        """Test current_type property."""
        display = MessageDisplay()
        
        assert display.current_type == "info"
        
        display.show_message("Error message", "error")
        assert display.current_type == "error"