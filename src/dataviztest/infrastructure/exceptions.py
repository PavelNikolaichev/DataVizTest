"""Custom exceptions for DataVizTest application.

This module defines the exception hierarchy for the application,
providing specific error types for different components.
"""

from typing import Any, Dict, List, Optional


class DataVizTestException(Exception):
    """Base exception for DataVizTest application.
    
    All custom exceptions should inherit from this class.
    """
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """Initialize the exception.
        
        Args:
            message: Error message
            details: Additional error details
            cause: Underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
    
    def __str__(self) -> str:
        """String representation of the exception."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} (Details: {details_str})"
        return self.message


class DataProcessingError(DataVizTestException):
    """Raised when data processing operations fail.
    
    This includes data loading, cleaning, validation, and transformation errors.
    """
    pass


class DataValidationError(DataProcessingError):
    """Raised when data validation fails.
    
    This is a specialized data processing error for validation issues.
    """
    
    def __init__(
        self, 
        message: str, 
        validation_errors: Optional[List[str]] = None,
        **kwargs
    ):
        """Initialize validation error.
        
        Args:
            message: Error message
            validation_errors: List of specific validation errors
            **kwargs: Additional arguments for parent class
        """
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []


class FilterError(DataVizTestException):
    """Raised when filter operations fail.
    
    This includes filter creation, application, and management errors.
    """
    pass


class InvalidFilterError(FilterError):
    """Raised when a filter configuration is invalid."""
    pass


class FilterApplicationError(FilterError):
    """Raised when applying filters to data fails."""
    pass


class VisualizationError(DataVizTestException):
    """Raised when visualization creation fails.
    
    This includes plot generation, rendering, and configuration errors.
    """
    pass


class PlotConfigurationError(VisualizationError):
    """Raised when plot configuration is invalid."""
    pass


class RenderingError(VisualizationError):
    """Raised when plot rendering fails."""
    pass


class GeospatialError(DataVizTestException):
    """Raised when geospatial operations fail.
    
    This includes geocoding, mapping, and coordinate transformation errors.
    """
    pass


class GeocodingError(GeospatialError):
    """Raised when geocoding operations fail."""
    pass


class MappingError(GeospatialError):
    """Raised when map creation or rendering fails."""
    pass


class UIError(DataVizTestException):
    """Raised when UI operations fail.
    
    This includes widget creation, interaction handling, and state management errors.
    """
    pass


class WidgetError(UIError):
    """Raised when widget operations fail."""
    pass


class StateError(DataVizTestException):
    """Raised when state management operations fail.
    
    This includes state transitions, serialization, and history management errors.
    """
    pass


class ConfigurationError(DataVizTestException):
    """Raised when configuration is invalid or missing."""
    pass


class ExportError(DataVizTestException):
    """Raised when data export operations fail."""
    pass


class CacheError(DataVizTestException):
    """Raised when cache operations fail."""
    pass


class EnvironmentError(DataVizTestException):
    """Raised when environment detection or setup fails."""
    pass


# Error context managers and utilities

class ErrorContext:
    """Context manager for error handling with additional context."""
    
    def __init__(
        self, 
        operation: str, 
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize error context.
        
        Args:
            operation: Description of the operation being performed
            context: Additional context information
        """
        self.operation = operation
        self.context = context or {}
    
    def __enter__(self):
        """Enter the context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and enhance any exceptions."""
        if exc_type and issubclass(exc_type, Exception):
            # If it's already a DataVizTestException, add context
            if isinstance(exc_val, DataVizTestException):
                exc_val.details.update(self.context)
                exc_val.details["operation"] = self.operation
            else:
                # Wrap other exceptions
                raise DataVizTestException(
                    f"Error during {self.operation}: {str(exc_val)}",
                    details=self.context,
                    cause=exc_val
                ) from exc_val
        return False


def handle_errors(operation: str, context: Optional[Dict[str, Any]] = None):
    """Decorator for error handling with context.
    
    Args:
        operation: Description of the operation
        context: Additional context information
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ErrorContext(operation, context):
                return func(*args, **kwargs)
        return wrapper
    return decorator