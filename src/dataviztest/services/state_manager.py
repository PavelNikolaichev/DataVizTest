"""State management for DataVizTest application.

This module provides state management functionality including state persistence,
undo/redo capabilities, and state synchronization across components.
"""

from __future__ import annotations

import copy
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from ..infrastructure import (
    StateError,
    get_logger,
    log_performance,
    handle_errors,
)
from ..models import FilterSet, PlotConfig


class ApplicationState:
    """Represents the complete application state at a point in time."""
    
    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        filtered_data: Optional[pd.DataFrame] = None,
        active_filters: Optional[List[FilterSet]] = None,
        current_selections: Optional[Dict[str, Any]] = None,
        ui_state: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """Initialize application state.
        
        Args:
            data: Original dataset
            filtered_data: Data after applying filters
            active_filters: Currently active filter sets
            current_selections: User selections and interactions
            ui_state: UI component states
            timestamp: State creation timestamp
        """
        self.data = data
        self.filtered_data = filtered_data
        self.active_filters = active_filters or []
        self.current_selections = current_selections or {}
        self.ui_state = ui_state or {}
        self.timestamp = timestamp or datetime.now()
    
    def copy(self) -> ApplicationState:
        """Create a deep copy of the state."""
        return ApplicationState(
            data=self.data.copy() if self.data is not None else None,
            filtered_data=self.filtered_data.copy() if self.filtered_data is not None else None,
            active_filters=copy.deepcopy(self.active_filters),
            current_selections=copy.deepcopy(self.current_selections),
            ui_state=copy.deepcopy(self.ui_state),
            timestamp=self.timestamp
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary representation.
        
        Returns:
            Dictionary representation of the state
        """
        return {
            "has_data": self.data is not None,
            "data_shape": self.data.shape if self.data is not None else None,
            "has_filtered_data": self.filtered_data is not None,
            "filtered_data_shape": self.filtered_data.shape if self.filtered_data is not None else None,
            "active_filters_count": len(self.active_filters),
            "selections_count": len(self.current_selections),
            "ui_components": list(self.ui_state.keys()),
            "timestamp": self.timestamp.isoformat()
        }


class StateManager:
    """Manages application state with history and persistence capabilities."""
    
    def __init__(self, max_history_size: int = 50):
        """Initialize the state manager.
        
        Args:
            max_history_size: Maximum number of states to keep in history
        """
        self.logger = get_logger(__name__)
        self.max_history_size = max_history_size
        
        # State management
        self._current_state = ApplicationState()
        self._state_history: List[ApplicationState] = []
        self._history_index = -1
        
        # State change listeners
        self._listeners: List[callable] = []
    
    @property
    def current_state(self) -> ApplicationState:
        """Get the current application state."""
        return self._current_state
    
    @property
    def can_undo(self) -> bool:
        """Check if undo operation is possible."""
        return self._history_index > 0
    
    @property
    def can_redo(self) -> bool:
        """Check if redo operation is possible."""
        return self._history_index < len(self._state_history) - 1
    
    def add_state_listener(self, callback: callable) -> None:
        """Add a callback to be notified of state changes.
        
        Args:
            callback: Function to call when state changes
        """
        self._listeners.append(callback)
    
    def remove_state_listener(self, callback: callable) -> None:
        """Remove a state change listener.
        
        Args:
            callback: Function to remove from listeners
        """
        if callback in self._listeners:
            self._listeners.remove(callback)
    
    def _notify_listeners(self) -> None:
        """Notify all listeners of state change."""
        for callback in self._listeners:
            try:
                callback(self._current_state)
            except Exception as e:
                self.logger.error(f"Error in state listener: {e}")
    
    @handle_errors("state update")
    def _save_state_to_history(self) -> None:
        """Save current state to history."""
        # Remove any future states if we're not at the end
        if self._history_index < len(self._state_history) - 1:
            self._state_history = self._state_history[:self._history_index + 1]
        
        # Add current state to history
        state_copy = self._current_state.copy()
        self._state_history.append(state_copy)
        self._history_index = len(self._state_history) - 1
        
        # Limit history size
        if len(self._state_history) > self.max_history_size:
            self._state_history.pop(0)
            self._history_index -= 1
        
        self.logger.debug(f"State saved to history. History size: {len(self._state_history)}")
    
    @log_performance
    @handle_errors("data update")
    def update_data(
        self, 
        data: pd.DataFrame, 
        save_to_history: bool = True
    ) -> None:
        """Update the main dataset.
        
        Args:
            data: New dataset
            save_to_history: Whether to save current state to history
        """
        if save_to_history:
            self._save_state_to_history()
        
        self._current_state.data = data.copy()
        self._current_state.filtered_data = None  # Reset filtered data
        self._current_state.timestamp = datetime.now()
        
        self.logger.info(f"Data updated: {data.shape}")
        self._notify_listeners()
    
    @handle_errors("filtered data update")
    def update_filtered_data(
        self, 
        filtered_data: pd.DataFrame,
        save_to_history: bool = True
    ) -> None:
        """Update the filtered dataset.
        
        Args:
            filtered_data: Filtered dataset
            save_to_history: Whether to save current state to history
        """
        if save_to_history:
            self._save_state_to_history()
        
        self._current_state.filtered_data = filtered_data.copy()
        self._current_state.timestamp = datetime.now()
        
        self.logger.info(f"Filtered data updated: {filtered_data.shape}")
        self._notify_listeners()
    
    @handle_errors("filters update")
    def update_filters(
        self, 
        filter_sets: List[FilterSet],
        save_to_history: bool = True
    ) -> None:
        """Update active filters.
        
        Args:
            filter_sets: List of active filter sets
            save_to_history: Whether to save current state to history
        """
        if save_to_history:
            self._save_state_to_history()
        
        self._current_state.active_filters = copy.deepcopy(filter_sets)
        self._current_state.timestamp = datetime.now()
        
        self.logger.info(f"Filters updated: {len(filter_sets)} filter sets")
        self._notify_listeners()
    
    @handle_errors("selections update")
    def update_selections(
        self, 
        selections: Dict[str, Any],
        save_to_history: bool = True
    ) -> None:
        """Update current selections.
        
        Args:
            selections: Dictionary of current selections
            save_to_history: Whether to save current state to history
        """
        if save_to_history:
            self._save_state_to_history()
        
        self._current_state.current_selections.update(selections)
        self._current_state.timestamp = datetime.now()
        
        self.logger.debug(f"Selections updated: {len(selections)} items")
        self._notify_listeners()
    
    @handle_errors("UI state update")
    def update_ui_state(
        self, 
        component_id: str, 
        state: Dict[str, Any],
        save_to_history: bool = False  # Usually don't save UI states to history
    ) -> None:
        """Update UI component state.
        
        Args:
            component_id: Identifier for the UI component
            state: Component state dictionary
            save_to_history: Whether to save current state to history
        """
        if save_to_history:
            self._save_state_to_history()
        
        self._current_state.ui_state[component_id] = copy.deepcopy(state)
        self._current_state.timestamp = datetime.now()
        
        self.logger.debug(f"UI state updated for component: {component_id}")
        self._notify_listeners()
    
    @handle_errors("undo operation")
    def undo(self) -> bool:
        """Undo to previous state.
        
        Returns:
            True if undo was successful, False otherwise
        """
        if not self.can_undo:
            return False
        
        self._history_index -= 1
        self._current_state = self._state_history[self._history_index].copy()
        
        self.logger.info(f"Undo successful. History index: {self._history_index}")
        self._notify_listeners()
        return True
    
    @handle_errors("redo operation")
    def redo(self) -> bool:
        """Redo to next state.
        
        Returns:
            True if redo was successful, False otherwise
        """
        if not self.can_redo:
            return False
        
        self._history_index += 1
        self._current_state = self._state_history[self._history_index].copy()
        
        self.logger.info(f"Redo successful. History index: {self._history_index}")
        self._notify_listeners()
        return True
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state.
        
        Returns:
            Dictionary with state summary information
        """
        return {
            "current_state": self._current_state.to_dict(),
            "history_size": len(self._state_history),
            "history_index": self._history_index,
            "can_undo": self.can_undo,
            "can_redo": self.can_redo,
            "listeners_count": len(self._listeners)
        }
    
    def clear_history(self) -> None:
        """Clear state history."""
        self._state_history.clear()
        self._history_index = -1
        self.logger.info("State history cleared")
    
    def reset_state(self) -> None:
        """Reset to initial empty state."""
        self._current_state = ApplicationState()
        self.clear_history()
        self.logger.info("State reset to initial state")
        self._notify_listeners()
    
    def get_data(self, use_filtered: bool = True) -> Optional[pd.DataFrame]:
        """Get current data (filtered or original).
        
        Args:
            use_filtered: Whether to return filtered data if available
            
        Returns:
            Current dataset or None if no data
        """
        if use_filtered and self._current_state.filtered_data is not None:
            return self._current_state.filtered_data
        return self._current_state.data