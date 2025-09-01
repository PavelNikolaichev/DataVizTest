"""Base widget classes for DataVizTest UI components.

This module provides the foundation for building interactive UI components
that work across different environments (Jupyter, Colab, standalone).
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union

import ipywidgets as widgets
from IPython.display import display, clear_output

from ...infrastructure import (
    UIError,
    WidgetError,
    get_logger,
    handle_errors,
    is_jupyter_environment,
)
from ...services import ApplicationService, StateManager, ApplicationState


class BaseWidget(ABC):
    """Abstract base class for all UI widgets."""
    
    def __init__(
        self,
        widget_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None
    ):
        """Initialize the base widget.
        
        Args:
            widget_id: Unique identifier for the widget
            title: Widget title
            description: Widget description
        """
        self.widget_id = widget_id or str(uuid.uuid4())
        self.title = title or self.__class__.__name__
        self.description = description
        self.logger = get_logger(__name__)
        
        # Widget state
        self._is_rendered = False
        self._is_enabled = True
        self._callbacks: Dict[str, List[Callable]] = {}
        
        # UI components
        self._container: Optional[widgets.Widget] = None
        self._output: Optional[widgets.Output] = None
        
        self.logger.debug(f"Created widget: {self.widget_id}")
    
    @property
    def is_rendered(self) -> bool:
        """Check if widget has been rendered."""
        return self._is_rendered
    
    @property
    def is_enabled(self) -> bool:
        """Check if widget is enabled."""
        return self._is_enabled
    
    @property
    def container(self) -> Optional[widgets.Widget]:
        """Get the main container widget."""
        return self._container
    
    def enable(self) -> None:
        """Enable the widget."""
        self._is_enabled = True
        self._update_enabled_state()
    
    def disable(self) -> None:
        """Disable the widget."""
        self._is_enabled = False
        self._update_enabled_state()
    
    def _update_enabled_state(self) -> None:
        """Update the enabled state of UI components."""
        if self._container:
            self._set_widget_enabled(self._container, self._is_enabled)
    
    def _set_widget_enabled(self, widget: widgets.Widget, enabled: bool) -> None:
        """Recursively set enabled state for widget and children."""
        try:
            if hasattr(widget, 'disabled'):
                widget.disabled = not enabled
            
            if hasattr(widget, 'children'):
                for child in widget.children:
                    self._set_widget_enabled(child, enabled)
        except Exception as e:
            self.logger.warning(f"Could not update enabled state: {e}")
    
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """Add a callback for widget events.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
        """
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable) -> None:
        """Remove a callback for widget events.
        
        Args:
            event_type: Type of event
            callback: Function to remove
        """
        if event_type in self._callbacks:
            try:
                self._callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    def _trigger_callbacks(self, event_type: str, *args, **kwargs) -> None:
        """Trigger callbacks for an event type.
        
        Args:
            event_type: Type of event that occurred
            *args: Arguments to pass to callbacks
            **kwargs: Keyword arguments to pass to callbacks
        """
        if event_type in self._callbacks:
            for callback in self._callbacks[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Error in callback: {e}")
    
    @abstractmethod
    def _create_widget(self) -> widgets.Widget:
        """Create the main widget component.
        
        Returns:
            IPython widget
        """
        pass
    
    @abstractmethod
    def _setup_interactions(self) -> None:
        """Set up widget interactions and event handlers."""
        pass
    
    @handle_errors("widget rendering")
    def render(self, container: Optional[widgets.Widget] = None) -> widgets.Widget:
        """Render the widget.
        
        Args:
            container: Optional container to render into
            
        Returns:
            Rendered widget
        """
        if self._is_rendered:
            return self._container
        
        # Create the main widget
        self._container = self._create_widget()
        
        # Set up interactions
        self._setup_interactions()
        
        # Create output widget for capturing displays
        self._output = widgets.Output()
        
        # Update enabled state
        self._update_enabled_state()
        
        self._is_rendered = True
        
        # Add to container if provided
        if container and hasattr(container, 'children'):
            container.children = container.children + (self._container,)
        
        self.logger.debug(f"Rendered widget: {self.widget_id}")
        return self._container
    
    def display(self) -> None:
        """Display the widget in the current output."""
        if not self._is_rendered:
            self.render()
        
        if is_jupyter_environment():
            display(self._container)
        else:
            self.logger.warning("Display called in non-Jupyter environment")
    
    def update(self, **kwargs) -> None:
        """Update widget state.
        
        Args:
            **kwargs: State updates
        """
        self.logger.debug(f"Updating widget {self.widget_id}")
        self._trigger_callbacks("update", **kwargs)
    
    def clear_output(self) -> None:
        """Clear the widget output."""
        if self._output:
            with self._output:
                clear_output(wait=True)
    
    def show_message(self, message: str, message_type: str = "info") -> None:
        """Show a message in the widget.
        
        Args:
            message: Message to display
            message_type: Type of message (info, warning, error, success)
        """
        if not self._output:
            return
        
        with self._output:
            color_map = {
                "info": "blue",
                "warning": "orange", 
                "error": "red",
                "success": "green"
            }
            
            color = color_map.get(message_type, "black")
            print(f"<span style='color: {color}'>{message}</span>")


class InteractiveWidget(BaseWidget):
    """Base class for interactive widgets that respond to user input."""
    
    def __init__(
        self,
        app_service: Optional[ApplicationService] = None,
        **kwargs
    ):
        """Initialize the interactive widget.
        
        Args:
            app_service: Application service for data operations
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.app_service = app_service
        self._state_data: Dict[str, Any] = {}
    
    def set_app_service(self, app_service: ApplicationService) -> None:
        """Set the application service.
        
        Args:
            app_service: Application service instance
        """
        self.app_service = app_service
        
        # Subscribe to state changes
        if hasattr(app_service, 'state_manager'):
            app_service.state_manager.add_state_listener(self._on_state_change)
    
    def _on_state_change(self, state: ApplicationState) -> None:
        """Handle application state changes.
        
        Args:
            state: New application state
        """
        self.logger.debug(f"State change received in widget {self.widget_id}")
        self._trigger_callbacks("state_change", state)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current widget state.
        
        Returns:
            Widget state dictionary
        """
        return self._state_data.copy()
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """Set widget state.
        
        Args:
            state: State dictionary to set
        """
        self._state_data.update(state)
        self._trigger_callbacks("state_set", state)


class ContainerWidget(BaseWidget):
    """Base class for widgets that contain other widgets."""
    
    def __init__(self, **kwargs):
        """Initialize the container widget."""
        super().__init__(**kwargs)
        self._child_widgets: List[BaseWidget] = []
    
    def add_widget(self, widget: BaseWidget) -> None:
        """Add a child widget.
        
        Args:
            widget: Widget to add
        """
        self._child_widgets.append(widget)
        
        # Re-render if already rendered
        if self._is_rendered:
            self._update_container()
    
    def remove_widget(self, widget: BaseWidget) -> None:
        """Remove a child widget.
        
        Args:
            widget: Widget to remove
        """
        if widget in self._child_widgets:
            self._child_widgets.remove(widget)
            
            # Re-render if already rendered
            if self._is_rendered:
                self._update_container()
    
    def clear_widgets(self) -> None:
        """Clear all child widgets."""
        self._child_widgets.clear()
        
        if self._is_rendered:
            self._update_container()
    
    @abstractmethod
    def _update_container(self) -> None:
        """Update the container with current child widgets."""
        pass
    
    def _create_widget(self) -> widgets.Widget:
        """Create container widget with children."""
        # Render all child widgets
        child_containers = []
        for child_widget in self._child_widgets:
            if not child_widget.is_rendered:
                child_widget.render()
            child_containers.append(child_widget.container)
        
        # Create appropriate container based on layout
        return self._create_container_widget(child_containers)
    
    @abstractmethod
    def _create_container_widget(self, children: List[widgets.Widget]) -> widgets.Widget:
        """Create the container widget with children.
        
        Args:
            children: List of child widgets
            
        Returns:
            Container widget
        """
        pass


class VBoxWidget(ContainerWidget):
    """Vertical box container widget."""
    
    def _create_container_widget(self, children: List[widgets.Widget]) -> widgets.Widget:
        """Create vertical box container."""
        return widgets.VBox(children)
    
    def _update_container(self) -> None:
        """Update the VBox container."""
        if self._container:
            child_containers = [
                child.container for child in self._child_widgets 
                if child.is_rendered and child.container
            ]
            self._container.children = child_containers
    
    def _setup_interactions(self) -> None:
        """Set up interactions for VBox."""
        pass


class HBoxWidget(ContainerWidget):
    """Horizontal box container widget."""
    
    def _create_container_widget(self, children: List[widgets.Widget]) -> widgets.Widget:
        """Create horizontal box container."""
        return widgets.HBox(children)
    
    def _update_container(self) -> None:
        """Update the HBox container."""
        if self._container:
            child_containers = [
                child.container for child in self._child_widgets 
                if child.is_rendered and child.container
            ]
            self._container.children = child_containers
    
    def _setup_interactions(self) -> None:
        """Set up interactions for HBox."""
        pass