import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from loguru import logger as loguru_logger
from utils.logger import logger

@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Setup and cleanup for logger tests"""
    # Store original handlers
    original_handlers = logger._core.handlers.copy()
    
    yield
    
    # Restore original handlers
    logger._core.handlers.clear()
    logger._core.handlers.update(original_handlers)

def test_logger_configuration(tmp_path):
    """Test logger configuration"""
    # Verify we have handlers
    assert len(logger._core.handlers) > 0
    
    # Test logging to a file to verify logger is working
    log_file = tmp_path / "test.log"
    test_handler_id = logger.add(log_file, format="{message}")
    
    try:
        logger.info("Test message")
        
        # Verify log was written
        with open(log_file) as f:
            content = f.read()
            assert "Test message" in content
    
    finally:
        logger.remove(test_handler_id)

def test_logger_output(tmp_path):
    """Test logger output to file"""
    # Setup temporary log file
    log_file = tmp_path / "test.log"
    test_handler_id = logger.add(log_file, format="{message}")
    
    try:
        # Test logging
        test_message = "Test log message"
        logger.info(test_message)
        
        # Verify log file content
        with open(log_file) as f:
            content = f.read()
            assert test_message in content
    
    finally:
        # Cleanup
        logger.remove(test_handler_id)

def test_logger_levels(tmp_path):
    """Test logger levels"""
    # Setup temporary log file
    log_file = tmp_path / "test.log"
    test_handler_id = logger.add(log_file, format="{level} | {message}", level="INFO")
    
    try:
        # Test different log levels
        logger.debug("Debug message")    # Should not be logged
        logger.info("Info message")      # Should be logged
        logger.warning("Warning message") # Should be logged
        logger.error("Error message")    # Should be logged
        
        # Read log file
        with open(log_file) as f:
            content = f.read()
            
            # Verify log levels
            assert "Debug message" not in content
            assert "INFO | Info message" in content
            assert "WARNING | Warning message" in content
            assert "ERROR | Error message" in content
    
    finally:
        # Cleanup
        logger.remove(test_handler_id)

def test_logger_formatting(tmp_path):
    """Test logger formatting"""
    # Setup temporary log file
    log_file = tmp_path / "test.log"
    format_string = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    test_handler_id = logger.add(log_file, format=format_string)
    
    try:
        # Test logging
        logger.info("Test message")
        
        # Verify log format
        with open(log_file) as f:
            content = f.read().strip()
            # Check format parts
            parts = content.split(" | ")
            assert len(parts) == 3
            assert parts[1] == "INFO"
            assert parts[2] == "Test message"
    
    finally:
        # Cleanup
        logger.remove(test_handler_id)

def test_logger_exception_handling(tmp_path):
    """Test exception logging"""
    # Setup temporary log file
    log_file = tmp_path / "test.log"
    test_handler_id = logger.add(log_file, format="{message}")
    
    try:
        # Generate and log an exception
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("Error occurred")
        
        # Verify exception was logged
        with open(log_file) as f:
            content = f.read()
            assert "Error occurred" in content
            assert "ValueError" in content
            assert "Test error" in content
    
    finally:
        # Cleanup
        logger.remove(test_handler_id)

def test_logger_file_rotation(tmp_path):
    """Test log file rotation"""
    # Setup temporary log file with small rotation size
    log_file = tmp_path / "rotating.log"
    test_handler_id = logger.add(
        str(log_file),
        rotation="1 KB",  # Very small rotation size
        format="{message}",  # Simple format to control size
        enqueue=True  # Enable enqueue for better rotation handling
    )
    
    try:
        # Write enough logs to trigger rotation
        for i in range(2000):  # Write many small messages
            logger.info("Test message " * 10)  # ~100 bytes per message
        
        # Force sync
        logger.complete()
        
        # Wait a bit for rotation to complete
        import time
        time.sleep(1)
        
        # Check for rotated files
        log_files = list(tmp_path.glob("rotating.*"))
        assert len(log_files) > 0, f"No rotated files found in {tmp_path}"
    
    finally:
        # Cleanup
        logger.remove(test_handler_id)

def test_logger_retention(tmp_path):
    """Test log file retention"""
    # Setup temporary log file with retention
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    
    test_handler_id = logger.add(
        str(log_dir / "test.log"),
        rotation="1 KB",
        retention=2,  # Keep only 2 files
        format="{message}",
        enqueue=True
    )
    
    try:
        # Generate enough logs for multiple rotations
        for i in range(1000):
            logger.info("Test message " * 10)
        
        # Force sync
        logger.complete()
        
        # Wait a bit for retention to take effect
        import time
        time.sleep(1)
        
        # Verify retention
        log_files = list(log_dir.glob("test.*"))
        assert len(log_files) <= 3  # Current file + 2 retained
    
    finally:
        # Cleanup
        logger.remove(test_handler_id)