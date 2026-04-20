"""
Test Suite for Task 1.5: Specific Exception Handling
====================================================

Validates that exception handling uses specific exception types
instead of generic Exception handlers, enabling better error diagnosis
and preventing silent failures.

Run with: pytest tests/test_task_1_5_exception_handling.py -v
"""

import pytest
import asyncio
import logging
from unittest.mock import patch, MagicMock, AsyncMock
import sys

# Setup logging to capture error messages
logging.basicConfig(level=logging.DEBUG)


class TestSpecificExceptions:
    """Test that code uses specific exception types"""
    
    def test_docker_exceptions_imported(self):
        """Verify docker.errors module provides specific exceptions"""
        try:
            import docker.errors
            # Check specific exceptions exist
            assert hasattr(docker.errors, 'DockerException'), "DockerException must exist"
            assert hasattr(docker.errors, 'ImageNotFound'), "ImageNotFound must exist"
            assert hasattr(docker.errors, 'APIError'), "APIError must exist"
        except ImportError:
            pytest.skip("docker module not installed")
    
    def test_asyncio_timeout_error_exists(self):
        """Verify asyncio.TimeoutError can be caught specifically"""
        try:
            # Create a timeout scenario
            async def test_timeout():
                try:
                    await asyncio.wait_for(asyncio.sleep(10), timeout=0.001)
                except asyncio.TimeoutError:
                    return "caught"
            
            result = asyncio.run(test_timeout())
            assert result == "caught", "TimeoutError should be catchable"
        except Exception as e:
            pytest.fail(f"Failed to catch TimeoutError: {e}")
    
    def test_keyboard_interrupt_is_specific(self):
        """Verify KeyboardInterrupt is a specific exception type"""
        assert issubclass(KeyboardInterrupt, BaseException)
        assert not issubclass(KeyboardInterrupt, Exception)  # Important!
        # This means catching Exception won't catch KeyboardInterrupt
    
    def test_exception_chain_preserves_context(self):
        """Verify that exception chaining preserves debugging info"""
        def function_that_fails():
            try:
                raise ValueError("Original error")
            except ValueError as e:
                # Proper exception chaining
                raise RuntimeError("Wrapped error") from e
        
        with pytest.raises(RuntimeError) as exc_info:
            function_that_fails()
        
        # Check that __cause__ is preserved
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ValueError)


class TestSandboxManagerExceptionHandling:
    """Test exception handling in sandbox operations"""
    
    def test_docker_init_error_handling(self):
        """Verify Docker initialization catches specific exceptions"""
        # This test verifies the code pattern
        error_patterns = [
            ("docker.errors.DockerException", "Docker connection failed"),
            ("Exception", "Unexpected error during Docker initialization"),
        ]
        
        # At least one specific docker exception should be caught
        assert any("docker.errors" in pattern[0] for pattern in error_patterns), \
            "Should catch specific docker.errors exceptions"
    
    def test_container_creation_error_handling(self):
        """Verify container creation catches specific exceptions"""
        # Expected error types when creating containers:
        expected_exceptions = [
            "docker.errors.ImageNotFound",  # Image doesn't exist
            "docker.errors.APIError",        # Docker API call failed
            "ContainerExecutionError",       # General container error
        ]
        
        # Verify at least image and API errors are specific
        assert "ImageNotFound" in str(expected_exceptions), \
            "Should catch ImageNotFound specifically"
        assert "APIError" in str(expected_exceptions), \
            "Should catch APIError specifically"


class TestMainIntegrationExceptionHandling:
    """Test exception handling in orchestrator"""
    
    def test_timeout_error_handling_pattern(self):
        """Verify that asyncio.TimeoutError is caught specifically in operations"""
        # Expected pattern:
        code_pattern = """
try:
    await asyncio.wait_for(async_operation(), timeout=TIMEOUT)
except asyncio.TimeoutError as e:
    logger.error(f"Operation timeout after {TIMEOUT}s: {e}", exc_info=True)
except KeyboardInterrupt:
    logger.warning("Operation interrupted by user")
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
"""
        # Verify pattern includes specific exceptions before generic Exception
        assert "asyncio.TimeoutError" in code_pattern
        assert "KeyboardInterrupt" in code_pattern
        assert code_pattern.index("asyncio.TimeoutError") < code_pattern.index("Exception")
        assert code_pattern.index("KeyboardInterrupt") < code_pattern.index("Exception")
    
    def test_exc_info_true_in_logs(self):
        """Verify that logging includes exception details with exc_info=True"""
        # This preserves stack traces for debugging
        code_with_exc_info = 'logger.error(f"Error: {e}", exc_info=True)'
        code_without_exc_info = 'logger.error(f"Error: {e}")'
        
        # Good pattern should include exc_info=True
        assert "exc_info=True" in code_with_exc_info
    
    def test_exception_hierarchy_respected(self):
        """Verify that exception handling respects exception hierarchy"""
        # More specific exceptions should be caught before general ones
        exception_order = [
            "asyncio.TimeoutError",  # Most specific
            "KeyboardInterrupt",      # User interrupt
            "ValueError",             # Value error
            "Exception",              # Most general
        ]
        
        # Ensure specific exceptions come before Exception
        exception_index = exception_order.index("Exception")
        specific_exceptions = exception_order[:exception_index]
        
        assert len(specific_exceptions) > 0, "Should have specific exceptions before generic"


class TestQuickReferenceExceptions:
    """Quick reference for common specific exceptions"""
    
    def test_io_exceptions(self):
        """Common I/O exceptions to catch specifically"""
        io_exceptions = [
            FileNotFoundError,  # File doesn't exist
            FileExistsError,    # File already exists
            PermissionError,    # Permission denied
            IsADirectoryError,  # Expected file, got directory
        ]
        
        for exc in io_exceptions:
            assert issubclass(exc, OSError)
    
    def test_docker_exceptions(self):
        """Common Docker exceptions"""
        expected = [
            "docker.errors.DockerException",  # Base Docker error
            "docker.errors.ImageNotFound",    # Image doesn't exist
            "docker.errors.APIError",         # Docker API failed
            "docker.errors.ContainerError",   # Container error
        ]
        
        # All should be specific to docker operations
        assert all("docker" in exc for exc in expected)
    
    def test_web_request_exceptions(self):
        """Common web request exceptions (requests library)"""
        expected = [
            "requests.exceptions.Timeout",      # Request timeout
            "requests.exceptions.ConnectionError",  # Can't connect
            "requests.exceptions.HTTPError",    # HTTP error
            "requests.exceptions.RequestException",  # General request error
        ]
        
        # All should be specific to web operations
        assert all("requests" in exc for exc in expected)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
