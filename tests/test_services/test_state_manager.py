"""Unit tests for StateManager class."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Any, Dict, List

from dataviztest.services.state_manager import StateManager, ApplicationState
from dataviztest.models import PlotConfig, PlotType, MapConfig, MapType, FilterSet
from dataviztest.infrastructure.exceptions import StateError


class TestApplicationState:
    """Test cases for ApplicationState."""
    
    def test_initialization_default(self):
        """Test ApplicationState initialization with defaults."""
        state = ApplicationState()
        
        assert state.data_loaded is False
        assert state.data_shape is None
        assert state.data_columns == []
        assert state.active_filters == []
        assert state.current_plot_config is None
        assert state.current_map_config is None
        assert isinstance(state.session_start, datetime)
        assert state.last_action is None
        assert state.error_count == 0
        assert state.metadata == {}
    
    def test_initialization_custom(self):
        """Test ApplicationState initialization with custom values."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        state = ApplicationState(
            data_loaded=True,
            data_shape=(100, 5),
            data_columns=['a', 'b', 'c'],
            session_start=custom_time,
            error_count=2,
            metadata={'test': 'value'}
        )
        
        assert state.data_loaded is True
        assert state.data_shape == (100, 5)
        assert state.data_columns == ['a', 'b', 'c']
        assert state.session_start == custom_time
        assert state.error_count == 2
        assert state.metadata == {'test': 'value'}
    
    def test_copy(self):
        """Test ApplicationState copy method."""
        original = ApplicationState(
            data_loaded=True,
            data_shape=(50, 3),
            data_columns=['x', 'y', 'z'],
            error_count=1,
            metadata={'key': 'value'}
        )
        
        copy_state = original.copy()
        
        # Verify copy is equal but not same object
        assert copy_state.data_loaded == original.data_loaded
        assert copy_state.data_shape == original.data_shape
        assert copy_state.data_columns == original.data_columns
        assert copy_state.error_count == original.error_count
        assert copy_state.metadata == original.metadata
        assert copy_state is not original
        assert copy_state.metadata is not original.metadata
    
    def test_to_dict(self):
        """Test ApplicationState to_dict method."""
        state = ApplicationState(
            data_loaded=True,
            data_shape=(10, 2),
            data_columns=['a', 'b'],
            error_count=3
        )
        
        result = state.to_dict()
        
        assert result['data_loaded'] is True
        assert result['data_shape'] == (10, 2)
        assert result['data_columns'] == ['a', 'b']
        assert result['error_count'] == 3
        assert 'session_start' in result
        assert isinstance(result['session_start'], datetime)


class TestStateManager:
    """Test cases for StateManager."""
    
    @pytest.fixture
    def state_manager(self):
        """Create StateManager instance for testing."""
        return StateManager()
    
    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        return pd.DataFrame({
            'id': range(1, 11),
            'name': [f'Item_{i}' for i in range(1, 11)],
            'value': range(10, 20)
        })
    
    def test_initialization(self, state_manager):
        """Test StateManager initialization."""
        assert state_manager.current_state is not None
        assert isinstance(state_manager.current_state, ApplicationState)
        assert state_manager._history == []
        assert state_manager._history_index == -1
        assert state_manager._max_history == 50
        assert state_manager._callbacks == {}
    
    def test_initialization_custom_history_size(self):
        """Test StateManager initialization with custom history size."""
        manager = StateManager(max_history=100)
        assert manager._max_history == 100
    
    def test_update_state_data_loaded(self, state_manager, sample_data):
        """Test state update when data is loaded."""
        # Execute
        state_manager.update_state(
            data=sample_data,
            action="data_loaded"
        )
        
        # Verify
        state = state_manager.current_state
        assert state.data_loaded is True
        assert state.data_shape == (10, 3)
        assert state.data_columns == ['id', 'name', 'value']
        assert state.last_action == "data_loaded"
    
    def test_update_state_filters_applied(self, state_manager):
        """Test state update when filters are applied."""
        # Setup
        filter_set = FilterSet(name="test_filter", filters=[])
        
        # Execute
        state_manager.update_state(
            filters=[filter_set],
            action="filters_applied"
        )
        
        # Verify
        state = state_manager.current_state
        assert len(state.active_filters) == 1
        assert state.active_filters[0] == filter_set
        assert state.last_action == "filters_applied"
    
    def test_update_state_plot_created(self, state_manager):
        """Test state update when plot is created."""
        # Setup
        plot_config = PlotConfig(
            plot_type=PlotType.SCATTER,
            columns={'x': 'id', 'y': 'value'}
        )
        
        # Execute
        state_manager.update_state(
            plot_config=plot_config,
            action="plot_created"
        )
        
        # Verify
        state = state_manager.current_state
        assert state.current_plot_config == plot_config
        assert state.last_action == "plot_created"
    
    def test_update_state_map_created(self, state_manager):
        """Test state update when map is created."""
        # Setup
        map_config = MapConfig(
            map_type=MapType.MARKER,
            location={'latitude_column': 'lat', 'longitude_column': 'lon'}
        )
        
        # Execute
        state_manager.update_state(
            map_config=map_config,
            action="map_created"
        )
        
        # Verify
        state = state_manager.current_state
        assert state.current_map_config == map_config
        assert state.last_action == "map_created"
    
    def test_update_state_error_incremented(self, state_manager):
        """Test state update when error occurs."""
        # Execute
        state_manager.update_state(
            action="error_occurred",
            error_occurred=True
        )
        
        # Verify
        state = state_manager.current_state
        assert state.error_count == 1
        assert state.last_action == "error_occurred"
    
    def test_update_state_metadata(self, state_manager):
        """Test state update with metadata."""
        # Execute
        state_manager.update_state(
            action="test_action",
            metadata={'custom_key': 'custom_value'}
        )
        
        # Verify
        state = state_manager.current_state
        assert state.metadata['custom_key'] == 'custom_value'
        assert state.last_action == "test_action"
    
    def test_update_state_history_saved(self, state_manager):
        """Test that state updates are saved to history."""
        # Initial state
        initial_error_count = state_manager.current_state.error_count
        
        # First update
        state_manager.update_state(action="action1")
        assert len(state_manager._history) == 1
        assert state_manager._history_index == 0
        
        # Second update with error
        state_manager.update_state(action="action2", error_occurred=True)
        assert len(state_manager._history) == 2
        assert state_manager._history_index == 1
        assert state_manager.current_state.error_count == initial_error_count + 1
    
    def test_update_state_history_limit(self):
        """Test that history respects maximum size limit."""
        # Create manager with small history limit
        manager = StateManager(max_history=3)
        
        # Add more updates than the limit
        for i in range(5):
            manager.update_state(action=f"action_{i}")
        
        # Verify history size is limited
        assert len(manager._history) == 3
        assert manager._history_index == 2
        
        # Verify latest states are kept
        assert manager._history[0].last_action == "action_2"
        assert manager._history[1].last_action == "action_3"
        assert manager._history[2].last_action == "action_4"
    
    def test_undo_success(self, state_manager):
        """Test successful undo operation."""
        # Setup - create some history
        state_manager.update_state(action="action1", error_occurred=True)
        state_manager.update_state(action="action2", error_occurred=True)
        
        # Get state before undo
        current_errors = state_manager.current_state.error_count
        
        # Execute undo
        result = state_manager.undo()
        
        # Verify
        assert result is True
        assert state_manager._history_index == 0
        assert state_manager.current_state.error_count == current_errors - 1
        assert state_manager.current_state.last_action == "action1"
    
    def test_undo_no_history(self, state_manager):
        """Test undo when no history is available."""
        # Execute undo without any history
        result = state_manager.undo()
        
        # Verify
        assert result is False
        assert state_manager._history_index == -1
    
    def test_redo_success(self, state_manager):
        """Test successful redo operation."""
        # Setup - create history and undo
        state_manager.update_state(action="action1")
        state_manager.update_state(action="action2", error_occurred=True)
        state_manager.undo()  # Go back to action1
        
        # Execute redo
        result = state_manager.redo()
        
        # Verify
        assert result is True
        assert state_manager._history_index == 1
        assert state_manager.current_state.last_action == "action2"
        assert state_manager.current_state.error_count == 1
    
    def test_redo_no_future_history(self, state_manager):
        """Test redo when no future history is available."""
        # Setup - create some history but don't undo
        state_manager.update_state(action="action1")
        
        # Execute redo without undoing first
        result = state_manager.redo()
        
        # Verify
        assert result is False
    
    def test_redo_after_new_update(self, state_manager):
        """Test redo after new update (should fail)."""
        # Setup - create history, undo, then new update
        state_manager.update_state(action="action1")
        state_manager.update_state(action="action2")
        state_manager.undo()  # Go back to action1
        state_manager.update_state(action="action3")  # New branch
        
        # Execute redo (should fail because history was modified)
        result = state_manager.redo()
        
        # Verify
        assert result is False
        assert state_manager.current_state.last_action == "action3"
    
    def test_add_callback(self, state_manager):
        """Test adding state change callback."""
        callback_called = False
        callback_state = None
        
        def test_callback(state):
            nonlocal callback_called, callback_state
            callback_called = True
            callback_state = state
        
        # Add callback
        callback_id = state_manager.add_callback("test", test_callback)
        
        # Trigger state change
        state_manager.update_state(action="test_action")
        
        # Verify callback was called
        assert callback_called is True
        assert callback_state is not None
        assert callback_state.last_action == "test_action"
        assert callback_id in state_manager._callbacks
    
    def test_remove_callback(self, state_manager):
        """Test removing state change callback."""
        def test_callback(state):
            pass
        
        # Add and then remove callback
        callback_id = state_manager.add_callback("test", test_callback)
        result = state_manager.remove_callback(callback_id)
        
        # Verify
        assert result is True
        assert callback_id not in state_manager._callbacks
    
    def test_remove_callback_nonexistent(self, state_manager):
        """Test removing non-existent callback."""
        result = state_manager.remove_callback("nonexistent_id")
        assert result is False
    
    def test_get_state_history(self, state_manager):
        """Test getting state history."""
        # Setup - create some history
        state_manager.update_state(action="action1")
        state_manager.update_state(action="action2")
        state_manager.update_state(action="action3")
        
        # Execute
        history = state_manager.get_state_history()
        
        # Verify
        assert len(history) == 3
        assert history[0].last_action == "action1"
        assert history[1].last_action == "action2"
        assert history[2].last_action == "action3"
    
    def test_get_state_history_limited(self, state_manager):
        """Test getting limited state history."""
        # Setup - create some history
        for i in range(5):
            state_manager.update_state(action=f"action_{i}")
        
        # Execute with limit
        history = state_manager.get_state_history(limit=3)
        
        # Verify
        assert len(history) == 3
        assert history[0].last_action == "action_2"  # Latest 3
        assert history[1].last_action == "action_3"
        assert history[2].last_action == "action_4"
    
    def test_clear_history(self, state_manager):
        """Test clearing state history."""
        # Setup - create some history
        state_manager.update_state(action="action1")
        state_manager.update_state(action="action2")
        
        # Execute
        state_manager.clear_history()
        
        # Verify
        assert state_manager._history == []
        assert state_manager._history_index == -1
    
    def test_can_undo(self, state_manager):
        """Test can_undo property."""
        # Initially no history
        assert state_manager.can_undo is False
        
        # After update
        state_manager.update_state(action="action1")
        assert state_manager.can_undo is True
        
        # After undo
        state_manager.undo()
        assert state_manager.can_undo is False
    
    def test_can_redo(self, state_manager):
        """Test can_redo property."""
        # Initially no history
        assert state_manager.can_redo is False
        
        # After update
        state_manager.update_state(action="action1")
        assert state_manager.can_redo is False
        
        # After undo
        state_manager.undo()
        assert state_manager.can_redo is True
        
        # After redo
        state_manager.redo()
        assert state_manager.can_redo is False
    
    def test_callback_error_handling(self, state_manager):
        """Test that callback errors don't break state updates."""
        def failing_callback(state):
            raise Exception("Callback error")
        
        # Add failing callback
        state_manager.add_callback("failing", failing_callback)
        
        # State update should still work despite callback error
        state_manager.update_state(action="test_action")
        
        # Verify state was updated
        assert state_manager.current_state.last_action == "test_action"