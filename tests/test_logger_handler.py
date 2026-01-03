"""Test the logger handler with console output support."""

import logging
import os
import uuid

import pytest

from src.logger_handler import LoggerHandler


def _get_unique_logger_name(prefix: str = "test") -> str:
    """Generate a unique logger name to avoid caching issues."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_logger_handler_initialization():
    """Test that LoggerHandler initializes without errors."""
    os.environ["COCKTAILBERRY_LOG_LEVEL"] = "DEBUG"
    logger_handler = LoggerHandler(_get_unique_logger_name())
    
    # Verify basic properties
    assert logger_handler.logger is not None
    assert logger_handler.logger_name is not None
    assert logger_handler.path is not None


def test_logger_methods_execute_without_error():
    """Test that all logger methods execute without errors."""
    os.environ["COCKTAILBERRY_LOG_LEVEL"] = "DEBUG"
    logger = LoggerHandler(_get_unique_logger_name("methods"))
    
    # These should not raise exceptions
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    logger.log_event("INFO", "Event message")
    logger.log_header("INFO", "Header message")


def test_logger_env_var_is_read():
    """Test that the environment variable is being read (indirect test via logger creation)."""
    # Set different log levels and create loggers
    test_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
    
    for level in test_levels:
        os.environ["COCKTAILBERRY_LOG_LEVEL"] = level
        logger = LoggerHandler(_get_unique_logger_name(level.lower()))
        # Just verify it doesn't crash
        logger.info(f"Testing with {level} level")
    
    # Test invalid level (should default to INFO)
    os.environ["COCKTAILBERRY_LOG_LEVEL"] = "INVALID_LEVEL"
    logger = LoggerHandler(_get_unique_logger_name("invalid"))
    logger.info("Testing with invalid level")


def test_logger_without_env_var():
    """Test that logger works when environment variable is not set."""
    # Remove env var if it exists
    os.environ.pop("COCKTAILBERRY_LOG_LEVEL", None)
    
    logger = LoggerHandler(_get_unique_logger_name("no_env"))
    
    # Should work with default settings
    logger.info("Testing without env var")
    logger.debug("Debug message")


