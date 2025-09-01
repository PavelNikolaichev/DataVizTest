"""Logging configuration for DataVizTest application.

This module provides centralized logging configuration that adapts to different
execution environments (Jupyter, Colab, standalone).
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .config import Settings, get_settings


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        """Format log record with colors."""
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    settings: Optional[Settings] = None
) -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None for console only)
        settings: Settings instance (uses global if None)
    """
    if settings is None:
        settings = get_settings()
    
    if level is None:
        level = settings.log_level
    
    if log_file is None:
        log_file = settings.log_file
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set root logger level
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Configure based on environment
    if settings.environment in ["jupyter", "colab"]:
        _setup_jupyter_logging(level, log_file)
    else:
        _setup_console_logging(level, log_file)
    
    # Set library loggers to higher level to reduce noise
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def _setup_jupyter_logging(level: str, log_file: Optional[str]) -> None:
    """Set up logging for Jupyter/Colab environments.
    
    Args:
        level: Logging level
        log_file: Optional log file path
    """
    # Simple format for Jupyter
    formatter = logging.Formatter(
        "[%(levelname)s] %(name)s: %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        _add_file_handler(log_file, level, formatter)


def _setup_console_logging(level: str, log_file: Optional[str]) -> None:
    """Set up logging for standalone console environments.
    
    Args:
        level: Logging level
        log_file: Optional log file path
    """
    # Detailed format for console
    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Colored formatter for console
    colored_formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(colored_formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        _add_file_handler(log_file, level, detailed_formatter)


def _add_file_handler(
    log_file: str, 
    level: str, 
    formatter: logging.Formatter
) -> None:
    """Add a file handler to the root logger.
    
    Args:
        log_file: Log file path
        level: Logging level
        formatter: Log formatter
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Rotating file handler to prevent huge log files
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, level.upper()))
    file_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_performance(func):
    """Decorator to log function execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    import time
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(
                f"{func.__name__} executed in {execution_time:.3f} seconds"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {execution_time:.3f} seconds: {e}"
            )
            raise
    
    return wrapper